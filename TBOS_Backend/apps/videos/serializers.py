from rest_framework import serializers

from apps.lessons.models import Lesson
from apps.videos.models import Video, YouTubePlaylistImport


# ──────────────────────────────────────────────
# Read serializers
# ──────────────────────────────────────────────


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight representation for list views."""

    playback_url = serializers.CharField(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "order",
            "source_type",
            "thumbnail",
            "duration_seconds",
            "is_preview",
            "playback_url",
        ]


class VideoDetailSerializer(serializers.ModelSerializer):
    """Full representation returned to both instructors and students."""

    playback_url = serializers.CharField(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "lesson",
            "course",
            "title",
            "description",
            "order",
            "source_type",
            "youtube_id",
            "cloudinary_public_id",
            "cloudinary_url",
            "s3_key",
            "s3_bucket",
            "s3_url",
            "thumbnail",
            "duration_seconds",
            "is_preview",
            "is_published",
            "playback_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "playback_url", "created_at", "updated_at"]


# Keep a backward-compatible alias used elsewhere in the app.
VideoSerializer = VideoDetailSerializer


# ──────────────────────────────────────────────
# Write serializers
# ──────────────────────────────────────────────


class VideoCreateSerializer(serializers.Serializer):
    """
    General-purpose create serializer.

    Validation rules:
    - source = YOUTUBE  → youtube_url required
    - source = CLOUDINARY → cloudinary_public_id + cloudinary_url required
    - source = AWS_S3   → s3_key + s3_bucket + s3_url required
    """

    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    title = serializers.CharField(max_length=300)
    video_source = serializers.ChoiceField(choices=Video.SourceType.choices)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    order = serializers.IntegerField(required=False, default=0, min_value=0)
    is_preview = serializers.BooleanField(required=False, default=False)
    duration_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    thumbnail = serializers.URLField(required=False, default="", allow_blank=True)

    # YouTube
    youtube_url = serializers.URLField(required=False, allow_blank=True, default="")

    # Cloudinary
    cloudinary_public_id = serializers.CharField(
        required=False, max_length=300, allow_blank=True, default=""
    )
    cloudinary_url = serializers.URLField(required=False, allow_blank=True, default="")

    # AWS S3
    s3_key = serializers.CharField(required=False, max_length=500, allow_blank=True, default="")
    s3_bucket = serializers.CharField(required=False, max_length=200, allow_blank=True, default="")
    s3_url = serializers.URLField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        source = attrs.get("video_source")
        if source == Video.SourceType.YOUTUBE:
            if not attrs.get("youtube_url"):
                raise serializers.ValidationError(
                    {"youtube_url": "Required when video_source is YOUTUBE."}
                )
        elif source == Video.SourceType.CLOUDINARY:
            if not attrs.get("cloudinary_public_id"):
                raise serializers.ValidationError(
                    {"cloudinary_public_id": "Required when video_source is CLOUDINARY."}
                )
            if not attrs.get("cloudinary_url"):
                raise serializers.ValidationError(
                    {"cloudinary_url": "Required when video_source is CLOUDINARY."}
                )
        elif source == Video.SourceType.AWS_S3:
            if not attrs.get("s3_key"):
                raise serializers.ValidationError(
                    {"s3_key": "Required when video_source is AWS_S3."}
                )
            if not attrs.get("s3_bucket"):
                raise serializers.ValidationError(
                    {"s3_bucket": "Required when video_source is AWS_S3."}
                )
            if not attrs.get("s3_url"):
                raise serializers.ValidationError(
                    {"s3_url": "Required when video_source is AWS_S3."}
                )
        return attrs


class VideoUpdateSerializer(serializers.ModelSerializer):
    """Allow updating title, preview status, and order."""

    class Meta:
        model = Video
        fields = ["title", "description", "is_preview", "order", "is_published"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "is_preview": {"required": False},
            "order": {"required": False},
            "is_published": {"required": False},
        }


# ──────────────────────────────────────────────
# Playlist import serializers
# ──────────────────────────────────────────────


class YouTubeImportSerializer(serializers.Serializer):
    """Import a single YouTube video into a lesson."""

    lesson_id = serializers.UUIDField()
    youtube_url = serializers.URLField()
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    order = serializers.IntegerField(required=False, default=0)
    is_preview = serializers.BooleanField(required=False, default=False)


class YouTubePlaylistImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = YouTubePlaylistImport
        fields = [
            "id",
            "course",
            "lesson",
            "playlist_url",
            "status",
            "videos_imported",
            "error_message",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "videos_imported",
            "error_message",
            "created_at",
        ]


# ──────────────────────────────────────────────
# Source-specific create serializers
# ──────────────────────────────────────────────


class CloudinaryVideoSerializer(serializers.Serializer):
    """Register a Cloudinary-hosted video."""

    lesson_id = serializers.UUIDField()
    title = serializers.CharField(max_length=300)
    cloudinary_public_id = serializers.CharField(max_length=300)
    cloudinary_url = serializers.URLField()
    description = serializers.CharField(required=False, default="", allow_blank=True)
    duration_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    thumbnail = serializers.URLField(required=False, default="", allow_blank=True)
    order = serializers.IntegerField(required=False, default=0, min_value=0)
    is_preview = serializers.BooleanField(required=False, default=False)


class S3VideoSerializer(serializers.Serializer):
    """Register an AWS S3-hosted video."""

    lesson_id = serializers.UUIDField()
    title = serializers.CharField(max_length=300)
    s3_key = serializers.CharField(max_length=500)
    s3_bucket = serializers.CharField(max_length=200)
    s3_url = serializers.URLField()
    description = serializers.CharField(required=False, default="", allow_blank=True)
    duration_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    thumbnail = serializers.URLField(required=False, default="", allow_blank=True)
    order = serializers.IntegerField(required=False, default=0, min_value=0)
    is_preview = serializers.BooleanField(required=False, default=False)

