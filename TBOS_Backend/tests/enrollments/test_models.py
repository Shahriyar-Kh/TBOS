"""Tests for enrollment models."""
import pytest

from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    LessonFactory,
    LessonProgressFactory,
    UserFactory,
    VideoFactory,
    VideoProgressFactory,
)


@pytest.mark.django_db
class TestEnrollmentModel:
    def test_create_enrollment(self):
        enrollment = EnrollmentFactory()
        assert enrollment.pk is not None
        assert enrollment.enrollment_status == Enrollment.EnrollmentStatus.ACTIVE
        assert enrollment.is_active is True
        assert enrollment.progress_percentage == 0

    def test_str_representation(self):
        enrollment = EnrollmentFactory()
        assert enrollment.student.email in str(enrollment)
        assert enrollment.course.title in str(enrollment)

    def test_unique_together_student_course(self):
        enrollment = EnrollmentFactory()
        with pytest.raises(Exception):
            EnrollmentFactory(student=enrollment.student, course=enrollment.course)

    def test_enrollment_status_choices(self):
        choices = [c[0] for c in Enrollment.EnrollmentStatus.choices]
        assert "active" in choices
        assert "completed" in choices
        assert "cancelled" in choices

    def test_defaults(self):
        enrollment = EnrollmentFactory()
        assert enrollment.completed_lessons_count == 0
        assert enrollment.total_lessons_count == 0
        assert enrollment.completed_at is None
        assert enrollment.last_accessed_at is None
        assert enrollment.enrolled_at is not None


@pytest.mark.django_db
class TestLessonProgressModel:
    def test_create_lesson_progress(self):
        lp = LessonProgressFactory()
        assert lp.pk is not None
        assert lp.is_completed is False
        assert lp.completed_at is None

    def test_str_representation(self):
        lp = LessonProgressFactory()
        assert lp.enrollment.student.email in str(lp)
        assert lp.lesson.title in str(lp)

    def test_unique_together_enrollment_lesson(self):
        lp = LessonProgressFactory()
        with pytest.raises(Exception):
            LessonProgressFactory(enrollment=lp.enrollment, lesson=lp.lesson)


@pytest.mark.django_db
class TestVideoProgressModel:
    def test_create_video_progress(self):
        vp = VideoProgressFactory()
        assert vp.pk is not None
        assert vp.watch_time_seconds == 0
        assert vp.last_position_seconds == 0
        assert vp.is_completed is False

    def test_str_representation(self):
        vp = VideoProgressFactory()
        assert vp.student.email in str(vp)
        assert vp.video.title in str(vp)

    def test_unique_together_student_video(self):
        vp = VideoProgressFactory()
        with pytest.raises(Exception):
            VideoProgressFactory(student=vp.student, video=vp.video)
