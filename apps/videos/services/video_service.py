import logging

import requests
from django.conf import settings

from apps.videos.models import Video, YouTubePlaylistImport

logger = logging.getLogger(__name__)


class VideoService:
    @staticmethod
    def import_single_youtube(lesson, youtube_url: str, title: str = "") -> Video:
        video_id = VideoService._extract_youtube_id(youtube_url)
        return Video.objects.create(
            lesson=lesson,
            title=title or f"YouTube Video {video_id}",
            source_type=Video.SourceType.YOUTUBE,
            youtube_video_id=video_id,
            order=lesson.videos.count(),
        )

    @staticmethod
    def import_youtube_playlist(playlist_import: YouTubePlaylistImport) -> None:
        """Fetch all videos from a YouTube playlist and create Video objects."""
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            playlist_import.status = "failed"
            playlist_import.error_message = "YouTube API key not configured."
            playlist_import.save()
            return

        playlist_id = playlist_import.playlist_id
        lesson = playlist_import.lesson
        next_page = ""
        imported_count = 0

        try:
            while True:
                url = (
                    f"https://www.googleapis.com/youtube/v3/playlistItems"
                    f"?part=snippet&maxResults=50&playlistId={playlist_id}"
                    f"&key={api_key}&pageToken={next_page}"
                )
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    snippet = item["snippet"]
                    yt_id = snippet["resourceId"]["videoId"]
                    if not Video.objects.filter(
                        lesson=lesson, youtube_video_id=yt_id
                    ).exists():
                        Video.objects.create(
                            lesson=lesson,
                            title=snippet.get("title", ""),
                            source_type=Video.SourceType.YOUTUBE,
                            youtube_video_id=yt_id,
                            order=lesson.videos.count(),
                        )
                        imported_count += 1

                next_page = data.get("nextPageToken", "")
                if not next_page:
                    break

            playlist_import.status = "completed"
            playlist_import.imported_count = imported_count
            playlist_import.save()

        except Exception as e:
            logger.error(f"YouTube playlist import failed: {e}")
            playlist_import.status = "failed"
            playlist_import.error_message = str(e)[:500]
            playlist_import.save()

    @staticmethod
    def _extract_youtube_id(url: str) -> str:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        return url
