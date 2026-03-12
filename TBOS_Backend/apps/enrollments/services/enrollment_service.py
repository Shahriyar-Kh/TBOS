import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Prefetch
from django.utils import timezone

from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
from apps.lessons.models import Lesson

logger = logging.getLogger(__name__)


class EnrollmentService:

    # ──────────────────────────────────────────────
    # Enrollment
    # ──────────────────────────────────────────────

    @staticmethod
    def enroll_student(student, course: Course) -> Enrollment:
        """Enroll a student in a course (free courses only via this path)."""
        if course.status != Course.Status.PUBLISHED:
            raise ValueError("Cannot enroll in a course that is not published.")
        if course.instructor == student:
            raise ValueError("Instructors cannot enroll in their own course.")
        if not course.is_free:
            raise ValueError("This course requires payment. Use /api/v1/payments/ instead.")

        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                "enrollment_status": Enrollment.EnrollmentStatus.ACTIVE,
                "total_lessons_count": EnrollmentService._count_course_lessons(course),
            },
        )
        if not created:
            raise ValueError("Already enrolled in this course.")

        course.total_enrollments += 1
        course.save(update_fields=["total_enrollments"])
        logger.info("Student %s enrolled in course %s", student.email, course.title)
        return enrollment

    @staticmethod
    def enroll_paid_course(student, course: Course) -> Enrollment:
        """Enroll via payments module — no is_free check."""
        if course.status != Course.Status.PUBLISHED:
            raise ValueError("Cannot enroll in a course that is not published.")
        if course.instructor == student:
            raise ValueError("Instructors cannot enroll in their own course.")

        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                "enrollment_status": Enrollment.EnrollmentStatus.ACTIVE,
                "total_lessons_count": EnrollmentService._count_course_lessons(course),
            },
        )
        if created:
            course.total_enrollments += 1
            course.save(update_fields=["total_enrollments"])
            logger.info("Paid enrollment: %s → %s", student.email, course.title)
        return enrollment

    # ──────────────────────────────────────────────
    # Access control
    # ──────────────────────────────────────────────

    @staticmethod
    def check_enrollment_access(student, course: Course) -> bool:
        """Return True if the student has an active enrollment in the course."""
        return Enrollment.objects.filter(
            student=student,
            course=course,
            is_active=True,
            enrollment_status=Enrollment.EnrollmentStatus.ACTIVE,
        ).exists()

    # ──────────────────────────────────────────────
    # Progress
    # ──────────────────────────────────────────────

    @staticmethod
    def calculate_course_progress(enrollment: Enrollment) -> Enrollment:
        """Recalculate progress percentage and completed count."""
        total = EnrollmentService._count_course_lessons(enrollment.course)
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        enrollment.total_lessons_count = total
        enrollment.completed_lessons_count = completed
        enrollment.progress_percentage = (
            (Decimal(completed) / Decimal(total) * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total
            else Decimal("0.00")
        )
        enrollment.last_accessed_at = timezone.now()

        if total and completed >= total:
            enrollment.enrollment_status = Enrollment.EnrollmentStatus.COMPLETED
            enrollment.completed_at = timezone.now()

        enrollment.save(update_fields=[
            "total_lessons_count",
            "completed_lessons_count",
            "progress_percentage",
            "last_accessed_at",
            "enrollment_status",
            "completed_at",
        ])
        return enrollment

    @staticmethod
    def mark_lesson_completed(enrollment: Enrollment, lesson: Lesson) -> Enrollment:
        """Mark a lesson as completed and recalculate course progress."""
        course = enrollment.course
        # Verify lesson belongs to the enrolled course
        if not course.sections.filter(lessons=lesson).exists():
            raise ValueError("Lesson does not belong to this course.")

        lp, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={"student": enrollment.student},
        )
        if not lp.student_id:
            lp.student = enrollment.student
        lp.is_completed = True
        lp.completed_at = timezone.now()
        lp.save(update_fields=["is_completed", "completed_at", "student", "updated_at"])

        return EnrollmentService.calculate_course_progress(enrollment)

    @staticmethod
    def update_video_progress(student, video, watch_time_seconds, last_position_seconds) -> VideoProgress:
        """Update or create video watch progress."""
        vp, _ = VideoProgress.objects.update_or_create(
            student=student,
            video=video,
            defaults={
                "watch_time_seconds": watch_time_seconds,
                "last_position_seconds": last_position_seconds,
                "is_completed": (
                    last_position_seconds >= video.duration_seconds * 0.9
                    if video.duration_seconds > 0
                    else False
                ),
            },
        )
        return vp

    # ──────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────

    @staticmethod
    def get_student_enrollments(student):
        """Return all enrollments for a student with course details."""
        return (
            Enrollment.objects.filter(student=student, is_active=True)
            .select_related(
                "course__category", "course__level", "course__instructor"
            )
            .order_by("-enrolled_at")
        )

    @staticmethod
    def get_course_students(course):
        """Return all enrollments for a course (for instructor view)."""
        return (
            Enrollment.objects.filter(course=course, is_active=True)
            .select_related("student")
            .order_by("-enrolled_at")
        )

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _count_course_lessons(course: Course) -> int:
        """Count total lessons across all sections of a course."""
        return Lesson.objects.filter(section__course=course).count()
