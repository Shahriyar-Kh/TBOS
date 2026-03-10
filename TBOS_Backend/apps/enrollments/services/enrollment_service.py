from django.utils import timezone

from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress
from apps.lessons.models import Lesson


class EnrollmentService:
    @staticmethod
    def enroll_free_course(student, course: Course) -> Enrollment:
        if not course.is_free:
            raise ValueError("This course requires payment.")

        enrollment, created = Enrollment.objects.get_or_create(
            student=student, course=course
        )
        if not created:
            raise ValueError("Already enrolled.")

        course.total_enrollments += 1
        course.save(update_fields=["total_enrollments"])
        return enrollment

    @staticmethod
    def enroll_paid_course(student, course: Course) -> Enrollment:
        enrollment, created = Enrollment.objects.get_or_create(
            student=student, course=course
        )
        if created:
            course.total_enrollments += 1
            course.save(update_fields=["total_enrollments"])
        return enrollment

    @staticmethod
    def complete_lesson(enrollment: Enrollment, lesson: Lesson) -> Enrollment:
        if lesson.course_id != enrollment.course_id:
            raise ValueError("Lesson not found in this course.")

        lp, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment, lesson=lesson
        )
        lp.is_completed = True
        lp.completed_at = timezone.now()
        lp.save()

        total_lessons = enrollment.course.lessons.count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        enrollment.progress_percent = (
            round(completed / total_lessons * 100, 2) if total_lessons else 0
        )
        enrollment.last_accessed_at = timezone.now()
        if enrollment.progress_percent >= 100:
            enrollment.completed_at = timezone.now()
        enrollment.save()

        return enrollment
