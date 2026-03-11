import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import api_error, api_success
from apps.core.mixins import APIResponseMixin
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdminOrInstructor, IsOwnerInstructor
from apps.enrollments.models import Enrollment
from apps.lessons.models import Lesson
from apps.videos.models import Video, YouTubePlaylistImport
from apps.videos.serializers import (
    CloudinaryVideoSerializer,
    S3VideoSerializer,
    VideoCreateSerializer,
    VideoDetailSerializer,
    VideoListSerializer,
    VideoUpdateSerializer,
    YouTubeImportSerializer,
    YouTubePlaylistImportSerializer,
)
from apps.videos.services.video_service import VideoService
from apps.videos.tasks import import_youtube_playlist

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Public / student: read videos for a lesson
# ──────────────────────────────────────────────────────────────


class LessonVideoView(APIResponseMixin, viewsets.ViewSet):
    """
    GET /api/v1/lessons/{lesson_id}/video/

    Preview rule:
    - is_preview=True  → anyone can watch
    - is_preview=False → authenticated & enrolled (or instructor/admin)
    """

    permission_classes = [AllowAny]

    def retrieve(self, request, lesson_pk=None):
        if getattr(self, "swagger_fake_view", False):
            return self.success_response(data=[], message="")
        try:
            lesson = (
                Lesson.objects.select_related("section__course").get(pk=lesson_pk)
            )
        except (Lesson.DoesNotExist, ValueError):
            raise NotFound("Lesson not found.")

        videos = (
            Video.objects.filter(lesson=lesson, is_published=True)
            .select_related("lesson", "course")
            .order_by("order")
        )

        # Determine access: preview-only vs full
        user = request.user
        can_access_all = False

        if user and user.is_authenticated:
            if user.role in ("admin", "instructor"):
                can_access_all = True
            elif user.role == "student":
                course = lesson.section.course
                can_access_all = Enrollment.objects.filter(
                    student=user, course=course, is_active=True
                ).exists()

        if not can_access_all:
            videos = videos.filter(is_preview=True)

        serializer = VideoListSerializer(videos, many=True)
        return self.success_response(
            data=serializer.data, message="Lesson videos retrieved successfully."
        )


# ──────────────────────────────────────────────────────────────
# Public: browse preview videos
# ──────────────────────────────────────────────────────────────


class PublicVideoViewSet(APIResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/videos/public/?lesson={id}&course={id}
    Only exposes is_preview=True videos for unauthenticated users.
    """

    serializer_class = VideoListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Video.objects.none()
        qs = Video.objects.filter(is_published=True, is_preview=True).select_related(
            "lesson", "course"
        )
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(
                data=paginated.data, message="Videos retrieved successfully."
            )
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(
            data=serializer.data, message="Videos retrieved successfully."
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = VideoDetailSerializer(instance)
        return self.success_response(
            data=serializer.data, message="Video retrieved successfully."
        )


# ──────────────────────────────────────────────────────────────
# Instructor: full CRUD + source-specific upload endpoints
# ──────────────────────────────────────────────────────────────


class InstructorVideoViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Instructor CRUD on videos.

    GET    /api/v1/videos/instructor/                    – list (filtered by lesson/course)
    GET    /api/v1/videos/instructor/{id}/               – detail
    PUT    /api/v1/videos/instructor/{id}/               – full update
    PATCH  /api/v1/videos/instructor/{id}/               – partial update
    DELETE /api/v1/videos/instructor/{id}/               – delete

    POST   /api/v1/videos/instructor/import-youtube/     – single YouTube
    POST   /api/v1/videos/instructor/import-playlist/    – playlist (async)
    POST   /api/v1/videos/instructor/add-cloudinary/     – Cloudinary
    POST   /api/v1/videos/instructor/add-s3/             – AWS S3
    POST   /api/v1/videos/instructor/reorder/            – reorder videos in a lesson
    """

    permission_classes = [IsAuthenticated, IsOwnerInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return VideoUpdateSerializer
        return VideoDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Video.objects.none()
        user = self.request.user
        qs = Video.objects.select_related("lesson__section__course", "course")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs.order_by("order")

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    # ── Standard CRUD responses ─────────────────────────────────

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VideoDetailSerializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(
                data=paginated.data, message="Videos retrieved successfully."
            )
        serializer = VideoDetailSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data, message="Videos retrieved successfully."
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = VideoDetailSerializer(instance)
        return self.success_response(
            data=serializer.data, message="Video retrieved successfully."
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = VideoUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return self.success_response(
            data=VideoDetailSerializer(instance).data,
            message="Video updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.success_response(message="Video deleted successfully.")

    # ── Helper: resolve lesson & check ownership ────────────────

    def _get_lesson_for_instructor(self, lesson_id):
        """
        Fetch a Lesson by PK, verifying the requesting instructor owns the course.
        Returns the lesson or raises PermissionDenied / NotFound.
        """
        try:
            lesson = Lesson.objects.select_related("section__course").get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise NotFound("Lesson not found.")
        user = self.request.user
        if user.role == "instructor" and lesson.section.course.instructor != user:
            raise PermissionDenied("You do not own this course.")
        return lesson

    # ── YouTube single video ────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="import-youtube")
    def import_youtube(self, request):
        """POST /api/v1/videos/instructor/import-youtube/"""
        serializer = YouTubeImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = self._get_lesson_for_instructor(data["lesson_id"])
        video = VideoService.create_youtube_video(
            lesson=lesson,
            youtube_url=data["youtube_url"],
            title=data["title"],
            description=data.get("description", ""),
            order=data.get("order", 0),
            is_preview=data.get("is_preview", False),
        )
        return self.created_response(
            data=VideoDetailSerializer(video).data,
            message="YouTube video added successfully.",
        )

    # ── YouTube playlist import (async) ────────────────────────

    @action(detail=False, methods=["post"], url_path="import-playlist")
    def import_playlist(self, request):
        """POST /api/v1/videos/instructor/import-playlist/"""
        serializer = YouTubePlaylistImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Verify the instructor owns the course
        lesson = self._get_lesson_for_instructor(
            str(serializer.validated_data["lesson"].id)
        )
        playlist_import = serializer.save(initiated_by=request.user)
        import_youtube_playlist.delay(str(playlist_import.id))
        return Response(
            {
                "success": True,
                "message": "Playlist import queued.",
                "data": YouTubePlaylistImportSerializer(playlist_import).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    # ── Cloudinary video ────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="add-cloudinary")
    def add_cloudinary(self, request):
        """POST /api/v1/videos/instructor/add-cloudinary/"""
        serializer = CloudinaryVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = self._get_lesson_for_instructor(data["lesson_id"])
        video = VideoService.upload_cloudinary_video(
            lesson=lesson,
            title=data["title"],
            cloudinary_public_id=data["cloudinary_public_id"],
            cloudinary_url=data["cloudinary_url"],
            description=data.get("description", ""),
            duration_seconds=data.get("duration_seconds", 0),
            thumbnail=data.get("thumbnail", ""),
            order=data.get("order", 0),
            is_preview=data.get("is_preview", False),
        )
        return self.created_response(
            data=VideoDetailSerializer(video).data,
            message="Cloudinary video added successfully.",
        )

    # ── AWS S3 video ────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="add-s3")
    def add_s3(self, request):
        """POST /api/v1/videos/instructor/add-s3/"""
        serializer = S3VideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = self._get_lesson_for_instructor(data["lesson_id"])
        video = VideoService.upload_s3_video(
            lesson=lesson,
            title=data["title"],
            s3_key=data["s3_key"],
            s3_bucket=data["s3_bucket"],
            s3_url=data["s3_url"],
            description=data.get("description", ""),
            duration_seconds=data.get("duration_seconds", 0),
            thumbnail=data.get("thumbnail", ""),
            order=data.get("order", 0),
            is_preview=data.get("is_preview", False),
        )
        return self.created_response(
            data=VideoDetailSerializer(video).data,
            message="S3 video added successfully.",
        )

    # ── Reorder videos in a lesson ──────────────────────────────

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """POST /api/v1/videos/instructor/reorder/
        Body: {"lesson_id": "<uuid>", "order": [{"id": "...", "order": 1}, ...]}
        """
        lesson_id = request.data.get("lesson_id")
        video_order = request.data.get("order", [])
        if not lesson_id:
            return api_error(
                message="lesson_id is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        lesson = self._get_lesson_for_instructor(lesson_id)
        for item in video_order:
            Video.objects.filter(id=item["id"], lesson=lesson).update(
                order=item["order"]
            )
        return self.success_response(message="Videos reordered successfully.")

