"""Tests for video API views."""
import pytest
from rest_framework import status

from apps.enrollments.models import Enrollment
from apps.lessons.models import Lesson
from apps.videos.models import Video
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    InstructorFactory,
    LessonFactory,
    VideoFactory,
)


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def course(db, instructor_user):
    return CourseFactory(instructor=instructor_user)


@pytest.fixture
def section(db, course):
    return CourseSectionFactory(course=course)


@pytest.fixture
def video_lesson(db, section):
    return LessonFactory(section=section, lesson_type=Lesson.LessonType.VIDEO)


@pytest.fixture
def video(db, video_lesson):
    return VideoFactory(
        lesson=video_lesson,
        course=video_lesson.section.course,
        source_type=Video.SourceType.YOUTUBE,
        youtube_id="dQw4w9WgXcQ",
    )


@pytest.fixture
def preview_video(db, video_lesson):
    return VideoFactory(
        lesson=video_lesson,
        course=video_lesson.section.course,
        is_preview=True,
        youtube_id="preview1234a",
    )


@pytest.fixture
def other_instructor(db):
    return InstructorFactory()


@pytest.fixture
def other_course(db, other_instructor):
    return CourseFactory(instructor=other_instructor)


@pytest.fixture
def other_section(db, other_course):
    return CourseSectionFactory(course=other_course)


@pytest.fixture
def other_lesson(db, other_section):
    return LessonFactory(section=other_section, lesson_type=Lesson.LessonType.VIDEO)


# ──────────────────────────────────────────────────────────────
# Public video listing
# ──────────────────────────────────────────────────────────────


class TestPublicVideoViewSet:
    def test_list_only_preview_videos(self, api_client, preview_video, video):
        response = api_client.get("/api/v1/videos/public/")
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]["results"]]
        assert str(preview_video.id) in ids
        assert str(video.id) not in ids

    def test_filter_by_lesson(self, api_client, preview_video, video_lesson):
        response = api_client.get(
            f"/api/v1/videos/public/?lesson={video_lesson.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]["results"]]
        assert str(preview_video.id) in ids


# ──────────────────────────────────────────────────────────────
# Student lesson video endpoint
# ──────────────────────────────────────────────────────────────


class TestLessonVideoView:
    def test_unauthenticated_sees_only_preview(
        self, api_client, video_lesson, preview_video, video
    ):
        response = api_client.get(f"/api/v1/lessons/{video_lesson.id}/video/")
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]]
        assert str(preview_video.id) in ids
        assert str(video.id) not in ids

    def test_enrolled_student_sees_all_videos(
        self, auth_client, student_user, video_lesson, preview_video, video
    ):
        course = video_lesson.section.course
        Enrollment.objects.create(student=student_user, course=course, is_active=True)
        response = auth_client.get(f"/api/v1/lessons/{video_lesson.id}/video/")
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]]
        assert str(preview_video.id) in ids
        assert str(video.id) in ids

    def test_unenrolled_student_sees_only_preview(
        self, auth_client, video_lesson, preview_video, video
    ):
        response = auth_client.get(f"/api/v1/lessons/{video_lesson.id}/video/")
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]]
        assert str(preview_video.id) in ids
        assert str(video.id) not in ids

    def test_instructor_sees_all_videos(
        self, instructor_client, video_lesson, preview_video, video
    ):
        response = instructor_client.get(f"/api/v1/lessons/{video_lesson.id}/video/")
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]]
        assert str(video.id) in ids

    def test_lesson_not_found_returns_404(self, api_client, db):
        import uuid
        response = api_client.get(f"/api/v1/lessons/{uuid.uuid4()}/video/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ──────────────────────────────────────────────────────────────
# Instructor: import single YouTube video
# ──────────────────────────────────────────────────────────────


class TestImportYouTube:
    def test_instructor_can_import_youtube(
        self, instructor_client, video_lesson
    ):
        payload = {
            "lesson_id": str(video_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Intro Video",
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert data["youtube_id"] == "dQw4w9WgXcQ"
        assert data["source_type"] == Video.SourceType.YOUTUBE
        assert "hqdefault.jpg" in data["thumbnail"]

    def test_import_requires_auth(self, api_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Intro",
        }
        response = api_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_import(self, auth_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Intro",
        }
        response = auth_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_import_to_other_course(
        self, instructor_client, other_lesson
    ):
        payload = {
            "lesson_id": str(other_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Intro",
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_youtube_url_rejected(self, instructor_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "OK",
        }
        # Corrupt the URL so ID extraction fails
        payload["youtube_url"] = "https://notyoutube.com/noid"
        response = instructor_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_video_lesson_rejected(self, instructor_client, section):
        article_lesson = LessonFactory(
            section=section, lesson_type=Lesson.LessonType.ARTICLE
        )
        payload = {
            "lesson_id": str(article_lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Intro",
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/import-youtube/", payload
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────────────────────
# Instructor: add Cloudinary video
# ──────────────────────────────────────────────────────────────


class TestAddCloudinaryVideo:
    def test_instructor_can_add_cloudinary(self, instructor_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "title": "Cloudinary Video",
            "cloudinary_public_id": "videos/sample",
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/sample.mp4",
            "duration_seconds": 120,
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/add-cloudinary/", payload
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert data["source_type"] == Video.SourceType.CLOUDINARY
        assert data["cloudinary_public_id"] == "videos/sample"

    def test_requires_auth(self, api_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "title": "Cloud",
            "cloudinary_public_id": "x",
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/x.mp4",
        }
        response = api_client.post(
            "/api/v1/videos/instructor/add-cloudinary/", payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_instructor_cannot_add_to_other_course(
        self, instructor_client, other_lesson
    ):
        payload = {
            "lesson_id": str(other_lesson.id),
            "title": "Cloud",
            "cloudinary_public_id": "x",
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/x.mp4",
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/add-cloudinary/", payload
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────────────────────
# Instructor: add AWS S3 video
# ──────────────────────────────────────────────────────────────


class TestAddS3Video:
    def test_instructor_can_add_s3(self, instructor_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "title": "S3 Video",
            "s3_key": "videos/test.mp4",
            "s3_bucket": "my-bucket",
            "s3_url": "https://my-bucket.s3.amazonaws.com/videos/test.mp4",
            "duration_seconds": 300,
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/add-s3/", payload
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert data["source_type"] == Video.SourceType.AWS_S3
        assert data["s3_bucket"] == "my-bucket"

    def test_requires_auth(self, api_client, video_lesson):
        payload = {
            "lesson_id": str(video_lesson.id),
            "title": "S3",
            "s3_key": "x",
            "s3_bucket": "b",
            "s3_url": "https://b.s3.amazonaws.com/x.mp4",
        }
        response = api_client.post(
            "/api/v1/videos/instructor/add-s3/", payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────────────────────
# Instructor: CRUD on existing videos
# ──────────────────────────────────────────────────────────────


class TestInstructorVideoCRUD:
    def test_list_videos_filtered_by_lesson(
        self, instructor_client, video_lesson, video, db
    ):
        # Create a video for a different lesson (should not appear)
        other_video = VideoFactory()
        response = instructor_client.get(
            f"/api/v1/videos/instructor/?lesson={video_lesson.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in response.data["data"]["results"]]
        assert str(video.id) in ids
        assert str(other_video.id) not in ids

    def test_update_video_title(self, instructor_client, video):
        response = instructor_client.patch(
            f"/api/v1/videos/instructor/{video.id}/",
            {"title": "Updated Title"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Title"

    def test_delete_video(self, instructor_client, video):
        response = instructor_client.delete(
            f"/api/v1/videos/instructor/{video.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not Video.objects.filter(id=video.id).exists()

    def test_instructor_cannot_update_other_course_video(
        self, instructor_client, other_lesson, db
    ):
        other_video = VideoFactory(
            lesson=other_lesson, course=other_lesson.section.course
        )
        response = instructor_client.patch(
            f"/api/v1/videos/instructor/{other_video.id}/",
            {"title": "Hacked Title"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reorder_videos(self, instructor_client, video_lesson, db):
        v1 = VideoFactory(
            lesson=video_lesson, course=video_lesson.section.course, order=1
        )
        v2 = VideoFactory(
            lesson=video_lesson, course=video_lesson.section.course, order=2
        )
        payload = {
            "lesson_id": str(video_lesson.id),
            "order": [
                {"id": str(v1.id), "order": 2},
                {"id": str(v2.id), "order": 1},
            ],
        }
        response = instructor_client.post(
            "/api/v1/videos/instructor/reorder/", payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        v1.refresh_from_db()
        v2.refresh_from_db()
        assert v1.order == 2
        assert v2.order == 1
