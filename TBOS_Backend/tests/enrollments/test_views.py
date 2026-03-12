"""Tests for enrollment API views."""
import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course
from apps.enrollments.models import Enrollment, VideoProgress
from tests.factories import (
    AdminFactory,
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    UserFactory,
    VideoFactory,
)

BASE = "/api/v1/enrollments"


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
def admin(db):
    return AdminFactory()


def auth(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def published_course(instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        is_free=True,
    )


@pytest.fixture
def course_with_lessons(published_course):
    section = CourseSectionFactory(course=published_course)
    lessons = [LessonFactory(section=section) for _ in range(3)]
    return published_course, section, lessons


# ──────────────────────────────────────────────
# Student: Enroll
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentEnroll:
    url = f"{BASE}/student/enroll/"

    def test_enroll_in_free_course(self, api_client, student, published_course):
        client = auth(api_client, student)
        response = client.post(self.url, {"course_id": str(published_course.id)})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert Enrollment.objects.filter(student=student, course=published_course).exists()

    def test_duplicate_enrollment_rejected(self, api_client, student, published_course):
        EnrollmentFactory(student=student, course=published_course)
        client = auth(api_client, student)
        response = client.post(self.url, {"course_id": str(published_course.id)})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_enroll_nonexistent_course(self, api_client, student):
        client = auth(api_client, student)
        response = client.post(
            self.url, {"course_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

    def test_enroll_requires_auth(self, api_client, published_course):
        response = api_client.post(self.url, {"course_id": str(published_course.id)})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_instructor_cannot_enroll(self, api_client, instructor, published_course):
        client = auth(api_client, instructor)
        response = client.post(self.url, {"course_id": str(published_course.id)})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_course_id_format(self, api_client, student):
        client = auth(api_client, student)
        response = client.post(self.url, {"course_id": "not-a-uuid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────
# Student: My courses (list)
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentMyCourses:
    url = f"{BASE}/student/"

    def test_list_enrolled_courses(self, api_client, student, published_course):
        EnrollmentFactory(student=student, course=published_course)
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]["results"]) == 1

    def test_excludes_other_students(self, api_client, student, published_course):
        other = UserFactory()
        EnrollmentFactory(student=other, course=published_course)
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 0

    def test_excludes_inactive_enrollments(self, api_client, student, published_course):
        EnrollmentFactory(student=student, course=published_course, is_active=False)
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 0

    def test_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# Student: Progress
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentProgress:
    def test_get_progress(self, api_client, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentFactory(student=student, course=course)
        client = auth(api_client, student)

        response = client.get(f"{BASE}/student/{enrollment.id}/progress/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["enrollment_id"] == str(enrollment.id)
        assert data["course_title"] == course.title

    def test_progress_requires_auth(self, api_client, student, published_course):
        enrollment = EnrollmentFactory(student=student, course=published_course)
        response = api_client.get(f"{BASE}/student/{enrollment.id}/progress/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# Student: Complete Lesson
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentCompleteLesson:
    def test_complete_lesson(self, api_client, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        enrollment = EnrollmentFactory(student=student, course=course)
        client = auth(api_client, student)

        response = client.post(
            f"{BASE}/student/{enrollment.id}/complete-lesson/",
            {"lesson_id": str(lessons[0].id)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_complete_nonexistent_lesson(self, api_client, student, published_course):
        enrollment = EnrollmentFactory(student=student, course=published_course)
        client = auth(api_client, student)

        response = client.post(
            f"{BASE}/student/{enrollment.id}/complete-lesson/",
            {"lesson_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_lesson_from_other_course(self, api_client, student, published_course):
        enrollment = EnrollmentFactory(student=student, course=published_course)
        other_course = CourseFactory(status=Course.Status.PUBLISHED)
        other_section = CourseSectionFactory(course=other_course)
        other_lesson = LessonFactory(section=other_section)
        client = auth(api_client, student)

        response = client.post(
            f"{BASE}/student/{enrollment.id}/complete-lesson/",
            {"lesson_id": str(other_lesson.id)},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────
# Student: Video Progress
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentVideoProgress:
    url = f"{BASE}/student/video-progress/"

    def test_update_video_progress(self, api_client, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        video = VideoFactory(lesson=lessons[0], course=course, duration_seconds=600)
        EnrollmentFactory(student=student, course=course)
        client = auth(api_client, student)

        response = client.post(
            self.url,
            {
                "video_id": str(video.id),
                "watch_time_seconds": 120,
                "last_position_seconds": 120,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert VideoProgress.objects.filter(student=student, video=video).exists()

    def test_reject_video_when_not_enrolled(self, api_client, student, course_with_lessons):
        course, section, lessons = course_with_lessons
        video = VideoFactory(lesson=lessons[0], course=course, duration_seconds=600)
        client = auth(api_client, student)

        response = client.post(
            self.url,
            {
                "video_id": str(video.id),
                "watch_time_seconds": 120,
                "last_position_seconds": 120,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_nonexistent_video(self, api_client, student):
        client = auth(api_client, student)
        response = client.post(
            self.url,
            {
                "video_id": "00000000-0000-0000-0000-000000000000",
                "watch_time_seconds": 120,
                "last_position_seconds": 120,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, api_client):
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# Instructor: Enrollments
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorEnrollments:
    url = f"{BASE}/instructor/"

    def test_list_enrollments_for_own_courses(
        self, api_client, instructor, published_course
    ):
        EnrollmentFactory(course=published_course)
        client = auth(api_client, instructor)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 1

    def test_excludes_other_instructors_courses(self, api_client, instructor):
        other_instructor = InstructorFactory()
        other_course = CourseFactory(
            instructor=other_instructor, status=Course.Status.PUBLISHED
        )
        EnrollmentFactory(course=other_course)
        client = auth(api_client, instructor)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 0

    def test_filter_by_course(self, api_client, instructor, published_course):
        EnrollmentFactory(course=published_course)
        client = auth(api_client, instructor)
        response = client.get(self.url, {"course": str(published_course.id)})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 1

    def test_requires_instructor_role(self, api_client, student):
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Admin: Enrollments
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAdminEnrollments:
    url = f"{BASE}/admin/"

    def test_list_all_enrollments(self, api_client, admin, published_course):
        EnrollmentFactory(course=published_course)
        EnrollmentFactory(course=published_course)
        client = auth(api_client, admin)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 2

    def test_filter_by_status(self, api_client, admin, published_course):
        EnrollmentFactory(
            course=published_course,
            enrollment_status=Enrollment.EnrollmentStatus.COMPLETED,
        )
        EnrollmentFactory(
            course=published_course,
            enrollment_status=Enrollment.EnrollmentStatus.ACTIVE,
        )
        client = auth(api_client, admin)
        response = client.get(self.url, {"status": "completed"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 1

    def test_filter_by_student(self, api_client, admin, published_course, student):
        EnrollmentFactory(student=student, course=published_course)
        EnrollmentFactory(course=published_course)  # different student
        client = auth(api_client, admin)
        response = client.get(self.url, {"student": str(student.id)})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 1

    def test_requires_admin_role(self, api_client, student):
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_access(self, api_client, instructor):
        client = auth(api_client, instructor)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
