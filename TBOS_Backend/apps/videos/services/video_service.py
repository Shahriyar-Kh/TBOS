import logging
import re

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError

from apps.lessons.models import Lesson
from apps.videos.models import Video, YouTubePlaylistImport

logger = logging.getLogger(__name__)

# Regex patterns for extracting YouTube video IDs
_YOUTUBE_ID_PATTERNS = [
    r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})",
]


class VideoService:
    # ─────────────────────────────────────────────
    # YouTube helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def extract_youtube_id(url: str) -> str:
        """Extract the 11-character video ID from any YouTube URL format."""
        for pattern in _YOUTUBE_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def generate_youtube_thumbnail(youtube_id: str) -> str:
        """Return the HQ thumbnail URL for a YouTube video ID."""
        return f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"

    # ─────────────────────────────────────────────
    # Validation helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _validate_video_lesson(lesson: Lesson) -> None:
        """Raise ValidationError if the lesson is not of VIDEO type."""
        if lesson.lesson_type != Lesson.LessonType.VIDEO:
            raise ValidationError(
                {"lesson": "Videos can only be added to lessons of type 'video'."}
            )

    # ─────────────────────────────────────────────
    # YouTube single video
    # ─────────────────────────────────────────────

    @staticmethod
    def create_youtube_video(
        lesson: Lesson,
        youtube_url: str,
        title: str,
        description: str = "",
        order: int = 0,
        is_preview: bool = False,
    ) -> Video:
        """Create a Video record for a single YouTube URL."""
        VideoService._validate_video_lesson(lesson)

        youtube_id = VideoService.extract_youtube_id(youtube_url)
        if not youtube_id:
            raise ValidationError({"youtube_url": "Invalid YouTube URL."})

        return Video.objects.create(
            lesson=lesson,
            course=lesson.section.course,
            title=title or f"YouTube Video {youtube_id}",
            description=description,
            order=order,
            is_preview=is_preview,
            source_type=Video.SourceType.YOUTUBE,
            youtube_id=youtube_id,
            thumbnail=VideoService.generate_youtube_thumbnail(youtube_id),
        )

    # ─────────────────────────────────────────────
    # YouTube playlist import
    # ─────────────────────────────────────────────

    @staticmethod
    def import_youtube_playlist(playlist_import: YouTubePlaylistImport) -> None:
        """Fetch all videos from a YouTube playlist and create Video objects."""
        api_key = getattr(settings, "YOUTUBE_API_KEY", "")
        if not api_key:
            playlist_import.status = YouTubePlaylistImport.ImportStatus.FAILED
            playlist_import.error_message = "YOUTUBE_API_KEY not configured."
            playlist_import.save(update_fields=["status", "error_message"])
            return

        import_re = re.search(r"list=([a-zA-Z0-9_-]+)", playlist_import.playlist_url)
        if not import_re:
            playlist_import.status = YouTubePlaylistImport.ImportStatus.FAILED
            playlist_import.error_message = "Could not extract playlist ID from URL."
            playlist_import.save(update_fields=["status", "error_message"])
            return

        playlist_id = import_re.group(1)
        lesson = playlist_import.lesson
        course = playlist_import.course
        next_page = ""
        order = Video.objects.filter(lesson=lesson).count()
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
                    if not Video.objects.filter(lesson=lesson, youtube_id=yt_id).exists():
                        Video.objects.create(
                            lesson=lesson,
                            course=course,
                            title=snippet.get("title", "Untitled"),
                            description=snippet.get("description", "")[:500],
                            order=order,
                            source_type=Video.SourceType.YOUTUBE,
                            youtube_id=yt_id,
                            thumbnail=VideoService.generate_youtube_thumbnail(yt_id),
                        )
                        order += 1
                        imported_count += 1

                next_page = data.get("nextPageToken", "")
                if not next_page:
                    break

            playlist_import.videos_imported = imported_count
            playlist_import.status = YouTubePlaylistImport.ImportStatus.COMPLETED
            playlist_import.save(update_fields=["status", "videos_imported"])

        except Exception as exc:
            logger.error("YouTube playlist import failed: %s", exc)
            playlist_import.status = YouTubePlaylistImport.ImportStatus.FAILED
            playlist_import.error_message = str(exc)[:500]
            playlist_import.save(update_fields=["status", "error_message"])

    # ─────────────────────────────────────────────
    # Cloudinary video
    # ─────────────────────────────────────────────

    @staticmethod
    def upload_cloudinary_video(
        lesson: Lesson,
        title: str,
        cloudinary_public_id: str,
        cloudinary_url: str,
        description: str = "",
        duration_seconds: int = 0,
        thumbnail: str = "",
        order: int = 0,
        is_preview: bool = False,
    ) -> Video:
        """Register a Cloudinary-hosted video for a lesson."""
        VideoService._validate_video_lesson(lesson)

        return Video.objects.create(
            lesson=lesson,
            course=lesson.section.course,
            title=title,
            description=description,
            order=order,
            is_preview=is_preview,
            source_type=Video.SourceType.CLOUDINARY,
            cloudinary_public_id=cloudinary_public_id,
            cloudinary_url=cloudinary_url,
            thumbnail=thumbnail,
            duration_seconds=duration_seconds,
        )

    # ─────────────────────────────────────────────
    # AWS S3 video
    # ─────────────────────────────────────────────

    @staticmethod
    def upload_s3_video(
        lesson: Lesson,
        title: str,
        s3_key: str,
        s3_bucket: str,
        s3_url: str,
        description: str = "",
        duration_seconds: int = 0,
        thumbnail: str = "",
        order: int = 0,
        is_preview: bool = False,
    ) -> Video:
        """Register an AWS S3-hosted video for a lesson."""
        VideoService._validate_video_lesson(lesson)

        return Video.objects.create(
            lesson=lesson,
            course=lesson.section.course,
            title=title,
            description=description,
            order=order,
            is_preview=is_preview,
            source_type=Video.SourceType.AWS_S3,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            s3_url=s3_url,
            thumbnail=thumbnail,
            duration_seconds=duration_seconds,
        )
