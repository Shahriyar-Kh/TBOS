from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.analytics.models import CourseAnalytics, UserActivity
from apps.analytics.services.cache_service import (
    admin_dashboard_key,
    get_dashboard_cache,
    instructor_dashboard_key,
    invalidate_admin_dashboard,
    invalidate_instructor_dashboard,
    invalidate_student_dashboard,
    set_dashboard_cache,
    student_dashboard_key,
)
from apps.analytics.services.realtime_service import (
    publish_admin_dashboard_update,
    publish_course_analytics_update,
    publish_instructor_dashboard_update,
    publish_student_dashboard_update,
)
from apps.assignments.models import AssignmentGrade, AssignmentSubmission
from apps.certificates.models import Certificate
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
from apps.payments.models import Order
from apps.quiz.models import QuizAttempt
from apps.reviews.models import Review

User = get_user_model()


def _safe_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def update_course_analytics(course_id=None):
    courses_qs = Course.objects.select_related("instructor").all()
    if course_id:
        courses_qs = courses_qs.filter(id=course_id)

    updated_items = []
    for course in courses_qs:
        enrollments_qs = Enrollment.objects.filter(course=course, is_active=True)

        average_progress = enrollments_qs.aggregate(avg=Avg("progress_percentage"))["avg"] or 0
        average_quiz_score = QuizAttempt.objects.filter(
            quiz__course=course,
            status__in=[QuizAttempt.Status.SUBMITTED, QuizAttempt.Status.EXPIRED],
        ).aggregate(avg=Avg("percentage"))["avg"] or 0
        average_assignment_score = AssignmentGrade.objects.filter(
            submission__assignment__course=course
        ).aggregate(avg=Avg("score"))["avg"] or 0
        total_revenue = Order.objects.filter(
            course=course,
            order_status=Order.OrderStatus.COMPLETED,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        rating_average = Review.objects.filter(
            course=course,
            status=Review.Status.PUBLISHED,
        ).aggregate(avg=Avg("rating"))["avg"] or 0

        latest_snapshot = CourseAnalytics.objects.filter(course=course).order_by("-last_updated").first()
        if latest_snapshot is None:
            latest_snapshot = CourseAnalytics(course=course)

        latest_snapshot.total_students = enrollments_qs.count()
        latest_snapshot.total_lessons = course.total_lessons
        latest_snapshot.completed_students = enrollments_qs.filter(
            Q(completed_at__isnull=False)
            | Q(enrollment_status=Enrollment.EnrollmentStatus.COMPLETED)
        ).count()
        latest_snapshot.average_progress = average_progress
        latest_snapshot.average_quiz_score = average_quiz_score
        latest_snapshot.average_assignment_score = average_assignment_score
        latest_snapshot.total_revenue = total_revenue
        latest_snapshot.rating_average = rating_average
        latest_snapshot.save()
        invalidate_instructor_dashboard(course.instructor_id)
        publish_course_analytics_update(
            str(course.id),
            {
                "course_id": str(course.id),
                "total_students": latest_snapshot.total_students,
                "average_progress": float(latest_snapshot.average_progress),
                "total_revenue": float(latest_snapshot.total_revenue),
                "rating_average": float(latest_snapshot.rating_average),
            },
        )
        publish_instructor_dashboard_update(
            str(course.instructor_id),
            {"course_id": str(course.id), "message": "Course analytics refreshed."},
        )
        updated_items.append(latest_snapshot)

    invalidate_admin_dashboard()
    publish_admin_dashboard_update({"updated_courses": len(updated_items)})
    return updated_items


def calculate_student_progress(user):
    enrollments_qs = Enrollment.objects.filter(student=user, is_active=True).select_related("course")
    completed_courses = enrollments_qs.filter(
        Q(completed_at__isnull=False) | Q(enrollment_status=Enrollment.EnrollmentStatus.COMPLETED)
    ).count()

    quiz_attempts_qs = QuizAttempt.objects.filter(
        student=user,
        status__in=[QuizAttempt.Status.SUBMITTED, QuizAttempt.Status.EXPIRED],
    )
    average_quiz_score = quiz_attempts_qs.aggregate(avg=Avg("percentage"))["avg"] or 0
    total_watch_seconds = VideoProgress.objects.filter(student=user).aggregate(
        total=Sum("watch_time_seconds")
    )["total"] or 0

    return {
        "courses_enrolled": enrollments_qs.count(),
        "courses_completed": completed_courses,
        "lessons_completed": LessonProgress.objects.filter(student=user, is_completed=True).count(),
        "quizzes_attempted": quiz_attempts_qs.count(),
        "assignments_submitted": AssignmentSubmission.objects.filter(student=user).count(),
        "certificates_earned": Certificate.objects.filter(student=user).count(),
        "learning_streak_days": _calculate_learning_streak(user),
        "learning_hours": round(total_watch_seconds / 3600, 2),
        "average_quiz_score": round(_safe_float(average_quiz_score), 2),
    }


def get_student_dashboard(user):
    cache_key = student_dashboard_key(user.id)
    cached = get_dashboard_cache(cache_key)
    if cached is not None:
        return cached

    payload = {
        "overview": calculate_student_progress(user),
        "insights": generate_learning_insights(user=user),
    }
    set_dashboard_cache(cache_key, payload)
    return payload


def get_instructor_dashboard(user):
    cache_key = instructor_dashboard_key(user.id)
    cached = get_dashboard_cache(cache_key)
    if cached is not None:
        return cached

    courses_qs = Course.objects.filter(instructor=user).prefetch_related("enrollments")
    enrollment_qs = Enrollment.objects.filter(course__instructor=user, is_active=True)
    completed_enrollments = enrollment_qs.filter(
        Q(completed_at__isnull=False) | Q(enrollment_status=Enrollment.EnrollmentStatus.COMPLETED)
    ).count()
    enrollment_count = enrollment_qs.count()

    lesson_progress_qs = LessonProgress.objects.filter(enrollment__course__instructor=user)
    lesson_progress_total = lesson_progress_qs.count()
    lesson_progress_done = lesson_progress_qs.filter(is_completed=True).count()

    total_revenue = Order.objects.filter(
        course__instructor=user,
        order_status=Order.OrderStatus.COMPLETED,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    average_rating = Review.objects.filter(
        course__instructor=user,
        status=Review.Status.PUBLISHED,
    ).aggregate(avg=Avg("rating"))["avg"] or 0

    quiz_performance = QuizAttempt.objects.filter(
        quiz__course__instructor=user,
        status__in=[QuizAttempt.Status.SUBMITTED, QuizAttempt.Status.EXPIRED],
    ).aggregate(avg=Avg("percentage"))["avg"] or 0

    payload = {
        "total_courses": courses_qs.count(),
        "total_students": enrollment_qs.values("student").distinct().count(),
        "total_revenue": total_revenue,
        "average_rating": round(_safe_float(average_rating), 2),
        "course_completion_rate": round(
            (completed_enrollments / enrollment_count * 100) if enrollment_count else 0,
            2,
        ),
        "lesson_completion_rate": round(
            (lesson_progress_done / lesson_progress_total * 100) if lesson_progress_total else 0,
            2,
        ),
        "quiz_performance": round(_safe_float(quiz_performance), 2),
        "assignment_submissions": AssignmentSubmission.objects.filter(
            assignment__course__instructor=user
        ).count(),
    }
    set_dashboard_cache(cache_key, payload)
    return payload


def get_admin_dashboard(start_date=None, end_date=None):
    cache_key = admin_dashboard_key(start_date=start_date, end_date=end_date)
    cached = get_dashboard_cache(cache_key)
    if cached is not None:
        return cached

    users_qs = User.objects.all()
    enrollments_qs = Enrollment.objects.filter(is_active=True)
    courses_qs = Course.objects.all()
    orders_qs = Order.objects.filter(order_status=Order.OrderStatus.COMPLETED)
    reviews_qs = Review.objects.filter(status=Review.Status.PUBLISHED)

    if start_date:
        users_qs = users_qs.filter(date_joined__date__gte=start_date)
        enrollments_qs = enrollments_qs.filter(enrolled_at__date__gte=start_date)
        courses_qs = courses_qs.filter(created_at__date__gte=start_date)
        orders_qs = orders_qs.filter(created_at__date__gte=start_date)
        reviews_qs = reviews_qs.filter(created_at__date__gte=start_date)
    if end_date:
        users_qs = users_qs.filter(date_joined__date__lte=end_date)
        enrollments_qs = enrollments_qs.filter(enrolled_at__date__lte=end_date)
        courses_qs = courses_qs.filter(created_at__date__lte=end_date)
        orders_qs = orders_qs.filter(created_at__date__lte=end_date)
        reviews_qs = reviews_qs.filter(created_at__date__lte=end_date)

    completed_enrollments = enrollments_qs.filter(
        Q(completed_at__isnull=False) | Q(enrollment_status=Enrollment.EnrollmentStatus.COMPLETED)
    ).count()
    enrollment_count = enrollments_qs.count()

    payload = {
        "total_users": users_qs.count(),
        "total_students": users_qs.filter(role=User.Role.STUDENT).count(),
        "total_instructors": users_qs.filter(role=User.Role.INSTRUCTOR).count(),
        "total_courses": courses_qs.count(),
        "total_enrollments": enrollment_count,
        "total_revenue": orders_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "course_completion_rate": round(
            (completed_enrollments / enrollment_count * 100) if enrollment_count else 0,
            2,
        ),
        "average_platform_rating": round(
            _safe_float(reviews_qs.aggregate(avg=Avg("rating"))["avg"]),
            2,
        ),
    }
    set_dashboard_cache(cache_key, payload)
    return payload


def record_user_activity(user, activity_type, reference_id=None, timestamp=None):
    activity = UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        reference_id=reference_id,
        timestamp=timestamp or timezone.now(),
    )
    invalidate_student_dashboard(user.id)
    invalidate_admin_dashboard()
    publish_student_dashboard_update(
        str(user.id),
        {
            "activity_type": activity.activity_type,
            "reference_id": str(activity.reference_id) if activity.reference_id else None,
            "timestamp": activity.timestamp.isoformat(),
        },
    )
    publish_admin_dashboard_update({"message": "User activity recorded."})
    return activity


def generate_learning_insights(user=None):
    course_completion_qs = Enrollment.objects.values("course").annotate(
        total_students=Count("id"),
        completed_students=Count(
            "id",
            filter=Q(
                Q(completed_at__isnull=False)
                | Q(enrollment_status=Enrollment.EnrollmentStatus.COMPLETED)
            ),
        ),
    )

    completion_lookup = {
        item["course"]: round(
            (item["completed_students"] / item["total_students"] * 100)
            if item["total_students"]
            else 0,
            2,
        )
        for item in course_completion_qs
    }

    popular_courses = list(
        Course.objects.annotate(student_count=Count("enrollments"))
        .order_by("-student_count")
        .values("id", "title", "student_count")[:5]
    )
    highest_revenue_courses = list(
        Course.objects.annotate(
            revenue=Sum(
                "orders__amount",
                filter=Q(orders__order_status=Order.OrderStatus.COMPLETED),
            )
        )
        .order_by("-revenue")
        .values("id", "title", "revenue")[:5]
    )

    course_titles = dict(Course.objects.values_list("id", "title"))
    highest_completion_courses = []
    for course_id, completion_rate in completion_lookup.items():
        highest_completion_courses.append(
            {
                "id": course_id,
                "title": course_titles.get(course_id, "Unknown Course"),
                "completion_rate": completion_rate,
            }
        )
    highest_completion_courses.sort(key=lambda x: x["completion_rate"], reverse=True)
    highest_completion_courses = highest_completion_courses[:5]

    activity_qs = UserActivity.objects.values("user").annotate(activity_count=Count("id"))
    if user is not None:
        activity_qs = activity_qs.filter(user=user)
    most_engaged_students = list(
        activity_qs.order_by("-activity_count")
        .values("user", "activity_count")[:5]
    )

    return {
        "most_popular_courses": popular_courses,
        "highest_completion_rate_courses": highest_completion_courses,
        "most_engaged_students": most_engaged_students,
        "highest_revenue_courses": highest_revenue_courses,
    }


def _calculate_learning_streak(user):
    activity_dates = list(
        UserActivity.objects.filter(user=user)
        .order_by("-timestamp")
        .values_list("timestamp", flat=True)
    )
    if not activity_dates:
        return 0

    unique_days = sorted({dt.date() for dt in activity_dates}, reverse=True)
    today = timezone.now().date()

    if unique_days[0] not in {today, today - timedelta(days=1)}:
        return 0

    streak = 1
    cursor = unique_days[0]
    for day in unique_days[1:]:
        if day == cursor - timedelta(days=1):
            streak += 1
            cursor = day
        elif day < cursor - timedelta(days=1):
            break
    return streak


class AnalyticsService:
    @staticmethod
    def update_course_analytics(course_id=None):
        return update_course_analytics(course_id=course_id)

    @staticmethod
    def calculate_student_progress(user):
        return calculate_student_progress(user)

    @staticmethod
    def get_student_dashboard(user):
        return get_student_dashboard(user)

    @staticmethod
    def get_instructor_dashboard(user):
        return get_instructor_dashboard(user)

    @staticmethod
    def get_admin_dashboard(start_date=None, end_date=None):
        return get_admin_dashboard(start_date=start_date, end_date=end_date)

    @staticmethod
    def record_user_activity(user, activity_type, reference_id=None, timestamp=None):
        return record_user_activity(
            user=user,
            activity_type=activity_type,
            reference_id=reference_id,
            timestamp=timestamp,
        )

    @staticmethod
    def generate_learning_insights(user=None):
        return generate_learning_insights(user=user)
