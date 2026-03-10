import re

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrInstructor
from apps.videos.models import Video, YouTubePlaylistImport
from apps.videos.serializers import (
    CloudinaryVideoSerializer,
    S3VideoSerializer,
    VideoSerializer,
    VideoListSerializer,
    YouTubeImportSerializer,
    YouTubePlaylistImportSerializer,
)
from apps.videos.tasks import import_youtube_playlist
from apps.lessons.models import Lesson


class PublicVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only video listing.
    GET /api/v1/videos/public/?lesson={id}
    Only shows preview videos for unauthenticated/non-enrolled users.
    """
    serializer_class = VideoListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Video.objects.filter(is_published=True, is_preview=True)
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class InstructorVideoViewSet(viewsets.ModelViewSet):
    """
    Instructor CRUD on videos.
    /api/v1/videos/instructor/
    """
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_queryset(self):
        user = self.request.user
        qs = Video.objects.select_related("lesson", "course")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    @action(detail=False, methods=["post"], url_path="import-youtube")
    def import_youtube(self, request):
        """Import a single YouTube video."""
        serializer = YouTubeImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = Lesson.objects.select_related("course").get(id=data["lesson_id"])
        if request.user.role == "instructor" and lesson.course.instructor != request.user:
            return Response(
                {"detail": "Not your course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        youtube_id = self._extract_youtube_id(data["youtube_url"])
        if not youtube_id:
            return Response(
                {"detail": "Invalid YouTube URL."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        video = Video.objects.create(
            lesson=lesson,
            course=lesson.course,
            title=data["title"],
            description=data.get("description", ""),
            order=data.get("order", 0),
            source_type=Video.SourceType.YOUTUBE,
            youtube_id=youtube_id,
            thumbnail=f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg",
            is_preview=data.get("is_preview", False),
        )
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="import-playlist")
    def import_playlist(self, request):
        """Queue a YouTube playlist import (async via Celery)."""
        serializer = YouTubePlaylistImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        playlist_import = serializer.save(initiated_by=request.user)
        import_youtube_playlist.delay(str(playlist_import.id))
        return Response(
            YouTubePlaylistImportSerializer(playlist_import).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"], url_path="add-cloudinary")
    def add_cloudinary(self, request):
        """Register a Cloudinary-hosted video."""
        serializer = CloudinaryVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = Lesson.objects.select_related("course").get(id=data["lesson_id"])

        video = Video.objects.create(
            lesson=lesson,
            course=lesson.course,
            title=data["title"],
            description=data.get("description", ""),
            order=data.get("order", 0),
            source_type=Video.SourceType.CLOUDINARY,
            cloudinary_public_id=data["cloudinary_public_id"],
            cloudinary_url=data["cloudinary_url"],
            thumbnail=data.get("thumbnail", ""),
            duration_seconds=data.get("duration_seconds", 0),
            is_preview=data.get("is_preview", False),
        )
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="add-s3")
    def add_s3(self, request):
        """Register an AWS S3-hosted video."""
        serializer = S3VideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = Lesson.objects.select_related("course").get(id=data["lesson_id"])

        video = Video.objects.create(
            lesson=lesson,
            course=lesson.course,
            title=data["title"],
            description=data.get("description", ""),
            order=data.get("order", 0),
            source_type=Video.SourceType.AWS_S3,
            s3_key=data["s3_key"],
            s3_bucket=data["s3_bucket"],
            s3_url=data["s3_url"],
            thumbnail=data.get("thumbnail", ""),
            duration_seconds=data.get("duration_seconds", 0),
            is_preview=data.get("is_preview", False),
        )
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _extract_youtube_id(url):
        patterns = [
            r"(?:v=|\/v\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
