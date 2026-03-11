"""Tests for the VideoService service layer."""
import pytest
from rest_framework.exceptions import ValidationError

from apps.lessons.models import Lesson
from apps.videos.models import Video
from apps.videos.services.video_service import VideoService
from tests.factories import LessonFactory, VideoFactory


@pytest.mark.django_db
class TestExtractYouTubeId:
    def test_standard_watch_url(self):
        assert VideoService.extract_youtube_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ) == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert (
            VideoService.extract_youtube_id("https://youtu.be/dQw4w9WgXcQ")
            == "dQw4w9WgXcQ"
        )

    def test_embed_url(self):
        assert (
            VideoService.extract_youtube_id(
                "https://www.youtube.com/embed/dQw4w9WgXcQ"
            )
            == "dQw4w9WgXcQ"
        )

    def test_invalid_url_returns_empty(self):
        assert VideoService.extract_youtube_id("https://example.com") == ""

    def test_url_with_extra_params(self):
        assert (
            VideoService.extract_youtube_id(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
            )
            == "dQw4w9WgXcQ"
        )


@pytest.mark.django_db
class TestGenerateYouTubeThumbnail:
    def test_generates_correct_url(self):
        assert (
            VideoService.generate_youtube_thumbnail("dQw4w9WgXcQ")
            == "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
        )


@pytest.mark.django_db
class TestCreateYouTubeVideo:
    def test_creates_video_with_correct_fields(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        video = VideoService.create_youtube_video(
            lesson=lesson,
            youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
        )
        assert video.pk is not None
        assert video.youtube_id == "dQw4w9WgXcQ"
        assert video.source_type == Video.SourceType.YOUTUBE
        assert "dQw4w9WgXcQ" in video.thumbnail
        assert video.lesson == lesson

    def test_auto_generates_thumbnail(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        video = VideoService.create_youtube_video(
            lesson=lesson,
            youtube_url="https://youtu.be/dQw4w9WgXcQ",
            title="Video",
        )
        assert video.thumbnail == "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"

    def test_invalid_url_raises_validation_error(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        with pytest.raises(ValidationError):
            VideoService.create_youtube_video(
                lesson=lesson,
                youtube_url="https://notayoutubeurl.com/video",
                title="Bad URL",
            )

    def test_non_video_lesson_raises_validation_error(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.ARTICLE)
        with pytest.raises(ValidationError):
            VideoService.create_youtube_video(
                lesson=lesson,
                youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                title="Test",
            )


@pytest.mark.django_db
class TestUploadCloudinaryVideo:
    def test_creates_cloudinary_video(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        video = VideoService.upload_cloudinary_video(
            lesson=lesson,
            title="Cloud Video",
            cloudinary_public_id="videos/sample",
            cloudinary_url="https://res.cloudinary.com/demo/video/upload/sample.mp4",
            duration_seconds=120,
        )
        assert video.pk is not None
        assert video.source_type == Video.SourceType.CLOUDINARY
        assert video.cloudinary_public_id == "videos/sample"
        assert video.duration_seconds == 120

    def test_non_video_lesson_raises_validation_error(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.QUIZ)
        with pytest.raises(ValidationError):
            VideoService.upload_cloudinary_video(
                lesson=lesson,
                title="Cloud Video",
                cloudinary_public_id="videos/sample",
                cloudinary_url="https://res.cloudinary.com/demo/video/upload/sample.mp4",
            )


@pytest.mark.django_db
class TestUploadS3Video:
    def test_creates_s3_video(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.VIDEO)
        video = VideoService.upload_s3_video(
            lesson=lesson,
            title="S3 Video",
            s3_key="videos/test.mp4",
            s3_bucket="my-bucket",
            s3_url="https://my-bucket.s3.amazonaws.com/videos/test.mp4",
            duration_seconds=200,
        )
        assert video.pk is not None
        assert video.source_type == Video.SourceType.AWS_S3
        assert video.s3_bucket == "my-bucket"
        assert video.s3_key == "videos/test.mp4"

    def test_non_video_lesson_raises_validation_error(self):
        lesson = LessonFactory(lesson_type=Lesson.LessonType.ASSIGNMENT)
        with pytest.raises(ValidationError):
            VideoService.upload_s3_video(
                lesson=lesson,
                title="S3 Video",
                s3_key="videos/test.mp4",
                s3_bucket="my-bucket",
                s3_url="https://my-bucket.s3.amazonaws.com/videos/test.mp4",
            )
