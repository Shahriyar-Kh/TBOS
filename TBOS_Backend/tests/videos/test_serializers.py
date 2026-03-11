"""Tests for video serializers."""
import pytest

from apps.lessons.models import Lesson
from apps.videos.models import Video
from apps.videos.serializers import (
    VideoCreateSerializer,
    VideoUpdateSerializer,
    CloudinaryVideoSerializer,
    S3VideoSerializer,
    YouTubeImportSerializer,
)
from tests.factories import LessonFactory


@pytest.mark.django_db
class TestVideoCreateSerializer:
    def test_youtube_valid(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "My Video",
            "video_source": Video.SourceType.YOUTUBE,
            "youtube_url": "https://www.youtube.com/watch?v=abc123abc12",
        }
        s = VideoCreateSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_youtube_missing_url_fails(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "My Video",
            "video_source": Video.SourceType.YOUTUBE,
        }
        s = VideoCreateSerializer(data=data)
        assert not s.is_valid()
        assert "youtube_url" in str(s.errors)

    def test_cloudinary_valid(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "Cloud Video",
            "video_source": Video.SourceType.CLOUDINARY,
            "cloudinary_public_id": "videos/sample",
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/sample.mp4",
        }
        s = VideoCreateSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_cloudinary_missing_fields_fails(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "Cloud Video",
            "video_source": Video.SourceType.CLOUDINARY,
        }
        s = VideoCreateSerializer(data=data)
        assert not s.is_valid()

    def test_s3_valid(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "S3 Video",
            "video_source": Video.SourceType.AWS_S3,
            "s3_key": "videos/my-video.mp4",
            "s3_bucket": "my-bucket",
            "s3_url": "https://my-bucket.s3.amazonaws.com/videos/my-video.mp4",
        }
        s = VideoCreateSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_s3_missing_fields_fails(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson": str(lesson.id),
            "title": "S3 Video",
            "video_source": Video.SourceType.AWS_S3,
        }
        s = VideoCreateSerializer(data=data)
        assert not s.is_valid()


@pytest.mark.django_db
class TestVideoUpdateSerializer:
    def test_partial_update_title(self):
        s = VideoUpdateSerializer(data={"title": "New Title"}, partial=True)
        assert s.is_valid(), s.errors
        assert s.validated_data["title"] == "New Title"

    def test_update_order(self):
        s = VideoUpdateSerializer(data={"order": 3}, partial=True)
        assert s.is_valid(), s.errors

    def test_update_is_preview(self):
        s = VideoUpdateSerializer(data={"is_preview": True}, partial=True)
        assert s.is_valid(), s.errors


@pytest.mark.django_db
class TestYouTubeImportSerializer:
    def test_valid_data(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson_id": str(lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=abc123abc12",
            "title": "My YT Video",
        }
        s = YouTubeImportSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_missing_title_fails(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson_id": str(lesson.id),
            "youtube_url": "https://www.youtube.com/watch?v=abc123abc12",
        }
        s = YouTubeImportSerializer(data=data)
        assert not s.is_valid()
        assert "title" in s.errors


@pytest.mark.django_db
class TestCloudinaryVideoSerializer:
    def test_valid_data(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson_id": str(lesson.id),
            "title": "Cloud Video",
            "cloudinary_public_id": "videos/demo",
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/demo.mp4",
        }
        s = CloudinaryVideoSerializer(data=data)
        assert s.is_valid(), s.errors


@pytest.mark.django_db
class TestS3VideoSerializer:
    def test_valid_data(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        data = {
            "lesson_id": str(lesson.id),
            "title": "S3 Video",
            "s3_key": "videos/test.mp4",
            "s3_bucket": "my-bucket",
            "s3_url": "https://my-bucket.s3.amazonaws.com/videos/test.mp4",
        }
        s = S3VideoSerializer(data=data)
        assert s.is_valid(), s.errors
