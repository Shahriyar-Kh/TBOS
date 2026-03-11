"""Tests for the Video model and YouTubePlaylistImport model."""
import pytest

from apps.lessons.models import Lesson
from apps.videos.models import Video, YouTubePlaylistImport
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    InstructorFactory,
    LessonFactory,
    VideoFactory,
    YouTubePlaylistImportFactory,
)


@pytest.mark.django_db
class TestVideoModel:
    def test_str_returns_title(self):
        video = VideoFactory(title="Intro to Django")
        assert str(video) == "Intro to Django"

    def test_default_source_type_is_youtube(self):
        video = VideoFactory()
        assert video.source_type == Video.SourceType.YOUTUBE

    def test_youtube_playback_url(self):
        video = VideoFactory(source_type=Video.SourceType.YOUTUBE, youtube_id="abc123")
        assert video.playback_url == "https://www.youtube.com/watch?v=abc123"

    def test_cloudinary_playback_url(self):
        video = VideoFactory(
            source_type=Video.SourceType.CLOUDINARY,
            cloudinary_url="https://res.cloudinary.com/demo/video/upload/v1/sample.mp4",
        )
        assert video.playback_url == "https://res.cloudinary.com/demo/video/upload/v1/sample.mp4"

    def test_s3_playback_url(self):
        video = VideoFactory(
            source_type=Video.SourceType.AWS_S3,
            s3_url="https://mybucket.s3.amazonaws.com/video.mp4",
        )
        assert video.playback_url == "https://mybucket.s3.amazonaws.com/video.mp4"

    def test_video_ordering(self, db):
        lesson = LessonFactory()
        v1 = VideoFactory(lesson=lesson, order=2, course=lesson.section.course)
        v2 = VideoFactory(lesson=lesson, order=1, course=lesson.section.course)
        videos = list(Video.objects.filter(lesson=lesson))
        assert videos[0] == v2
        assert videos[1] == v1

    def test_video_cascade_delete_with_lesson(self):
        video = VideoFactory()
        lesson_id = video.lesson_id
        video.lesson.delete()
        assert not Video.objects.filter(lesson_id=lesson_id).exists()

    def test_is_preview_default_false(self):
        video = VideoFactory()
        assert video.is_preview is False

    def test_is_published_default_true(self):
        video = VideoFactory()
        assert video.is_published is True


@pytest.mark.django_db
class TestYouTubePlaylistImportModel:
    def test_str_includes_course_and_status(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)
        lesson = LessonFactory(section=CourseSectionFactory(course=course))
        pl = YouTubePlaylistImportFactory(course=course, lesson=lesson)
        result = str(pl)
        assert course.title in result
        assert "pending" in result

    def test_default_status_is_pending(self):
        pl = YouTubePlaylistImportFactory()
        assert pl.status == YouTubePlaylistImport.ImportStatus.PENDING

    def test_status_choices(self):
        statuses = [s[0] for s in YouTubePlaylistImport.ImportStatus.choices]
        assert "pending" in statuses
        assert "processing" in statuses
        assert "completed" in statuses
        assert "failed" in statuses
