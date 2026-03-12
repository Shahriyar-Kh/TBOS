"""Tests for enrollment service layer."""
import pytest
from decimal import Decimal

from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
from apps.enrollments.services.enrollment_service import EnrollmentService
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    UserFactory,
    VideoFactory,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def published_course(db, instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        is_free=True,
    )


@pytest.fixture
def paid_course(db, instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        is_free=False,
        price=49.99,
    )


@pytest.fixture
def draft_course(db, instructor):
    return CourseFactory(instructor=instructor, status=Course.Status.DRAFT)


@pytest.fixture
def course_with_lessons(published_course):
    section = CourseSectionFactory(course=published_course)
    lessons = [LessonFactory(section=section) for _ in range(3)]
    return published_course, section, lessons


# ──────────────────────────────────────────────
# enroll_student
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestEnrollStudent:
    def test_enroll_in_free_published_course(self, student, published_course):
        enrollment = EnrollmentService.enroll_student(student, published_course)
        assert enrollment.student == student
        assert enrollment.course == published_course
        assert enrollment.enrollment_status == Enrollment.EnrollmentStatus.ACTIVE

    def test_increments_total_enrollments(self, student, published_course):
        published_course.total_enrollments = 0
        published_course.save()
        EnrollmentService.enroll_student(student, published_course)
        published_course.refresh_from_db()
        assert published_course.total_enrollments == 1

    def test_sets_total_lessons_count(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentService.enroll_student(student, course)
        assert enrollment.total_lessons_count == len(lessons)

    def test_reject_duplicate_enrollment(self, student, published_course):
        EnrollmentService.enroll_student(student, published_course)
        with pytest.raises(ValueError, match="Already enrolled"):
            EnrollmentService.enroll_student(student, published_course)

    def test_reject_draft_course(self, student, draft_course):
        with pytest.raises(ValueError, match="not published"):
            EnrollmentService.enroll_student(student, draft_course)

    def test_reject_instructor_self_enrollment(self, instructor, published_course):
        with pytest.raises(ValueError, match="cannot enroll"):
            EnrollmentService.enroll_student(instructor, published_course)

    def test_reject_paid_course(self, student, paid_course):
        with pytest.raises(ValueError, match="payment"):
            EnrollmentService.enroll_student(student, paid_course)


# ──────────────────────────────────────────────
# enroll_paid_course
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestEnrollPaidCourse:
    def test_enroll_in_paid_course(self, student, paid_course):
        enrollment = EnrollmentService.enroll_paid_course(student, paid_course)
        assert enrollment.student == student
        assert enrollment.enrollment_status == Enrollment.EnrollmentStatus.ACTIVE

    def test_idempotent_for_existing(self, student, paid_course):
        e1 = EnrollmentService.enroll_paid_course(student, paid_course)
        e2 = EnrollmentService.enroll_paid_course(student, paid_course)
        assert e1.pk == e2.pk

    def test_reject_draft_course(self, student, draft_course):
        with pytest.raises(ValueError, match="not published"):
            EnrollmentService.enroll_paid_course(student, draft_course)


# ──────────────────────────────────────────────
# check_enrollment_access
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCheckEnrollmentAccess:
    def test_returns_true_for_active_enrollment(self, student, published_course):
        EnrollmentFactory(
            student=student,
            course=published_course,
            enrollment_status=Enrollment.EnrollmentStatus.ACTIVE,
        )
        assert EnrollmentService.check_enrollment_access(student, published_course) is True

    def test_returns_false_when_not_enrolled(self, student, published_course):
        assert EnrollmentService.check_enrollment_access(student, published_course) is False

    def test_returns_false_for_cancelled(self, student, published_course):
        EnrollmentFactory(
            student=student,
            course=published_course,
            enrollment_status=Enrollment.EnrollmentStatus.CANCELLED,
            is_active=False,
        )
        assert EnrollmentService.check_enrollment_access(student, published_course) is False


# ──────────────────────────────────────────────
# mark_lesson_completed & calculate_course_progress
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestMarkLessonCompleted:
    def test_mark_lesson_completed(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentFactory(student=student, course=course)

        updated = EnrollmentService.mark_lesson_completed(enrollment, lessons[0])
        assert updated.completed_lessons_count == 1
        assert updated.progress_percentage == Decimal("33.33")

    def test_mark_all_lessons_completed(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentFactory(student=student, course=course)

        for lesson in lessons:
            enrollment = EnrollmentService.mark_lesson_completed(enrollment, lesson)

        assert enrollment.completed_lessons_count == 3
        assert enrollment.progress_percentage == Decimal("100.00")
        assert enrollment.enrollment_status == Enrollment.EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None

    def test_rejects_lesson_from_other_course(self, student, published_course):
        enrollment = EnrollmentFactory(student=student, course=published_course)
        other_course = CourseFactory(status=Course.Status.PUBLISHED)
        other_section = CourseSectionFactory(course=other_course)
        other_lesson = LessonFactory(section=other_section)

        with pytest.raises(ValueError, match="does not belong"):
            EnrollmentService.mark_lesson_completed(enrollment, other_lesson)

    def test_idempotent_lesson_completion(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentFactory(student=student, course=course)

        EnrollmentService.mark_lesson_completed(enrollment, lessons[0])
        enrollment = EnrollmentService.mark_lesson_completed(enrollment, lessons[0])
        assert enrollment.completed_lessons_count == 1


# ──────────────────────────────────────────────
# update_video_progress
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateVideoProgress:
    def test_create_video_progress(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        video = VideoFactory(lesson=lessons[0], course=course, duration_seconds=600)

        vp = EnrollmentService.update_video_progress(student, video, 300, 300)
        assert vp.watch_time_seconds == 300
        assert vp.last_position_seconds == 300
        assert vp.is_completed is False

    def test_auto_complete_at_90_percent(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        video = VideoFactory(lesson=lessons[0], course=course, duration_seconds=100)

        vp = EnrollmentService.update_video_progress(student, video, 95, 95)
        assert vp.is_completed is True

    def test_update_existing_progress(self, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        video = VideoFactory(lesson=lessons[0], course=course, duration_seconds=600)

        EnrollmentService.update_video_progress(student, video, 100, 100)
        vp = EnrollmentService.update_video_progress(student, video, 400, 400)
        assert vp.watch_time_seconds == 400
        assert VideoProgress.objects.filter(student=student, video=video).count() == 1


# ──────────────────────────────────────────────
# Query helpers
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestQueryHelpers:
    def test_get_student_enrollments(self, student, published_course):
        EnrollmentFactory(student=student, course=published_course)
        qs = EnrollmentService.get_student_enrollments(student)
        assert qs.count() == 1

    def test_get_student_enrollments_excludes_inactive(self, student, published_course):
        EnrollmentFactory(student=student, course=published_course, is_active=False)
        qs = EnrollmentService.get_student_enrollments(student)
        assert qs.count() == 0

    def test_get_course_students(self, published_course):
        for _ in range(3):
            EnrollmentFactory(course=published_course)
        qs = EnrollmentService.get_course_students(published_course)
        assert qs.count() == 3
