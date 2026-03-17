from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework import status

from apps.analytics.models import UserActivity
from tests.factories import (
    AssignmentSubmissionFactory,
    CertificateFactory,
    CourseFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    LessonProgressFactory,
    OrderFactory,
    QuizAttemptFactory,
    ReviewFactory,
    UserFactory,
    VideoFactory,
    VideoProgressFactory,
)

BASE = "/api/v1/analytics"


@pytest.fixture
def auth(api_client, access_token_for_user):
    def _auth(user):
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(user)}")
        return api_client

    return _auth


@pytest.mark.django_db
class TestStudentDashboardView:
    url = f"{BASE}/student/dashboard/"

    def test_student_dashboard_returns_expected_metrics(self, auth, student_user):
        course = CourseFactory(status="published")
        enrollment = EnrollmentFactory(
            student=student_user,
            course=course,
            enrollment_status="completed",
            progress_percentage=100,
            completed_at=timezone.now(),
            is_active=True,
        )
        lesson = LessonFactory(section__course=course)
        video = VideoFactory(course=course, lesson=lesson, duration_seconds=3600)

        LessonProgressFactory(enrollment=enrollment, student=student_user, lesson=lesson, is_completed=True)
        QuizAttemptFactory(
            quiz__course=course,
            student=student_user,
            status="submitted",
            percentage=80,
        )
        AssignmentSubmissionFactory(
            assignment__course=course,
            student=student_user,
            status="submitted",
        )
        CertificateFactory(student=student_user, course=course)
        VideoProgressFactory(student=student_user, video=video, watch_time_seconds=7200)

        UserActivity.objects.create(
            user=student_user,
            activity_type=UserActivity.ActivityType.LOGIN,
            timestamp=timezone.now(),
        )
        UserActivity.objects.create(
            user=student_user,
            activity_type=UserActivity.ActivityType.VIDEO_WATCH,
            timestamp=timezone.now() - timedelta(days=1),
        )

        response = auth(student_user).get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        overview = response.data["data"]["overview"]
        assert overview["courses_enrolled"] == 1
        assert overview["courses_completed"] == 1
        assert overview["lessons_completed"] == 1
        assert overview["quizzes_attempted"] == 1
        assert overview["assignments_submitted"] == 1
        assert overview["certificates_earned"] == 1
        assert overview["average_quiz_score"] == 80.0
        assert overview["learning_hours"] == 2.0

    def test_non_student_cannot_access_student_dashboard(self, auth):
        instructor = InstructorFactory()
        response = auth(instructor).get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestInstructorAnalyticsViews:
    dashboard_url = f"{BASE}/instructor/dashboard/"

    def test_instructor_dashboard_returns_metrics(self, auth):
        instructor = InstructorFactory()
        student = UserFactory()
        course = CourseFactory(instructor=instructor, status="published")
        enrollment = EnrollmentFactory(student=student, course=course, is_active=True)
        lesson = LessonFactory(section__course=course)

        LessonProgressFactory(enrollment=enrollment, student=student, lesson=lesson, is_completed=True)
        QuizAttemptFactory(
            quiz__course=course,
            student=student,
            status="submitted",
            percentage=70,
        )
        AssignmentSubmissionFactory(
            assignment__course=course,
            student=student,
            status="submitted",
        )
        ReviewFactory(course=course, student=student, rating=4)
        OrderFactory(
            student=student,
            course=course,
            order_status="COMPLETED",
            amount=120,
        )

        response = auth(instructor).get(self.dashboard_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["total_courses"] == 1
        assert data["total_students"] == 1
        assert float(data["total_revenue"]) == 120.0
        assert data["average_rating"] == 4.0
        assert data["assignment_submissions"] == 1

    def test_instructor_cannot_access_other_course_analytics(self, auth):
        owner = InstructorFactory()
        other_instructor = InstructorFactory()
        course = CourseFactory(instructor=owner, status="published")

        response = auth(other_instructor).get(f"{BASE}/instructor/course/{course.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminAnalyticsViews:
    dashboard_url = f"{BASE}/admin/dashboard/"
    revenue_url = f"{BASE}/admin/revenue/"

    def test_admin_dashboard_access_and_core_metrics(self, auth, admin_user):
        instructor = InstructorFactory()
        student = UserFactory()
        course = CourseFactory(instructor=instructor, status="published")
        EnrollmentFactory(student=student, course=course, is_active=True)
        OrderFactory(student=student, course=course, order_status="COMPLETED", amount=55)
        ReviewFactory(course=course, student=student, rating=5)

        response = auth(admin_user).get(self.dashboard_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["total_users"] >= 3
        assert data["total_courses"] >= 1
        assert float(data["total_revenue"]) >= 55.0
        assert "insights" in data

    def test_revenue_endpoint_supports_date_filtering(self, auth, admin_user):
        instructor = InstructorFactory()
        course_old = CourseFactory(instructor=instructor, status="published")
        course_new = CourseFactory(instructor=instructor, status="published")
        student_old = UserFactory()
        student_new = UserFactory()

        old_order = OrderFactory(
            student=student_old,
            course=course_old,
            order_status="COMPLETED",
            amount=40,
        )
        new_order = OrderFactory(
            student=student_new,
            course=course_new,
            order_status="COMPLETED",
            amount=80,
        )

        old_date = timezone.now() - timedelta(days=14)
        new_date = timezone.now() - timedelta(days=1)
        old_order.created_at = old_date
        old_order.save(update_fields=["created_at"])
        new_order.created_at = new_date
        new_order.save(update_fields=["created_at"])

        start_date = (timezone.now() - timedelta(days=7)).date().isoformat()
        response = auth(admin_user).get(self.revenue_url, {"start_date": start_date})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert float(data["total_revenue"]) == 80.0
        assert data["total_orders"] == 1


@pytest.mark.django_db
class TestActivityTrackingView:
    url = f"{BASE}/activity/"

    def test_record_activity_creates_user_activity(self, auth, student_user):
        payload = {
            "activity_type": UserActivity.ActivityType.QUIZ_ATTEMPT,
            "reference_id": str(uuid4()),
        }

        response = auth(student_user).post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert UserActivity.objects.filter(user=student_user).count() == 1

    def test_activity_endpoint_requires_auth(self, api_client):
        response = api_client.post(
            self.url,
            {"activity_type": UserActivity.ActivityType.LOGIN},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
