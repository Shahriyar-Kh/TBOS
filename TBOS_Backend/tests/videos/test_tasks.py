from unittest.mock import MagicMock, patch

import pytest

from apps.videos.models import Video, YouTubePlaylistImport
from apps.videos.tasks import import_youtube_playlist
from tests.factories import CourseFactory, LessonFactory, YouTubePlaylistImportFactory


@pytest.mark.django_db
class TestVideoTasks:
    def test_import_youtube_playlist_fails_when_api_key_missing(self, settings):
        settings.YOUTUBE_API_KEY = ""
        playlist_import = YouTubePlaylistImportFactory()

        import_youtube_playlist.run(str(playlist_import.id))

        playlist_import.refresh_from_db()
        assert playlist_import.status == YouTubePlaylistImport.ImportStatus.FAILED
        assert "not configured" in playlist_import.error_message.lower()

    def test_import_youtube_playlist_fails_for_invalid_playlist_url(self, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        playlist_import = YouTubePlaylistImportFactory(playlist_url="https://youtube.com/watch?v=abc")

        import_youtube_playlist.run(str(playlist_import.id))

        playlist_import.refresh_from_db()
        assert playlist_import.status == YouTubePlaylistImport.ImportStatus.FAILED
        assert "extract playlist id" in playlist_import.error_message.lower()

    @patch("requests.get")
    def test_import_youtube_playlist_creates_videos_on_success(self, mocked_get, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        lesson = LessonFactory()
        course = lesson.section.course
        playlist_import = YouTubePlaylistImportFactory(
            course=course,
            lesson=lesson,
            playlist_url="https://www.youtube.com/playlist?list=PL123",
        )

        response = MagicMock()
        response.json.return_value = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "abc123"},
                        "title": "Intro",
                        "description": "desc",
                    }
                }
            ]
        }
        mocked_get.return_value = response

        import_youtube_playlist.run(str(playlist_import.id))

        playlist_import.refresh_from_db()
        assert playlist_import.status == YouTubePlaylistImport.ImportStatus.COMPLETED
        assert playlist_import.videos_imported == 1
        assert Video.objects.filter(lesson=lesson, youtube_id="abc123").exists()

    @patch("apps.videos.tasks.import_youtube_playlist.retry", side_effect=RuntimeError("retry"))
    def test_import_youtube_playlist_retries_on_unexpected_exception(self, _mocked_retry, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        with pytest.raises(RuntimeError, match="retry"):
            import_youtube_playlist.run("11111111-1111-1111-1111-111111111111")
