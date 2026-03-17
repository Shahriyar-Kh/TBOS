import pytest

from tests.factories import CourseFactory, EnrollmentFactory, QuizAttemptFactory, UserFactory, VideoFactory, VideoProgressFactory


@pytest.mark.django_db
class TestPerformanceSmoke:
    def test_multiple_enrollments_bulk_creation(self):
        course = CourseFactory(status="published", is_free=True)
        students = [UserFactory() for _ in range(20)]

        for student in students:
            EnrollmentFactory(student=student, course=course)

        assert course.enrollments.count() == 20

    def test_multiple_quiz_submissions_records(self):
        attempts = [QuizAttemptFactory(status="submitted") for _ in range(25)]
        assert len(attempts) == 25

    def test_multiple_video_progress_updates(self):
        student = UserFactory()
        videos = [VideoFactory() for _ in range(15)]

        for idx, video in enumerate(videos, start=1):
            VideoProgressFactory(student=student, video=video, watch_time_seconds=idx * 10)

        assert student.video_progress.count() == 15
