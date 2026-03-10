from rest_framework import serializers

from apps.videos.models import Video, YouTubePlaylistImport


class VideoSerializer(serializers.ModelSerializer):
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


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight for listings."""
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


class YouTubeImportSerializer(serializers.Serializer):
    """Import a single YouTube video into a lesson."""
    lesson_id = serializers.UUIDField()
    youtube_url = serializers.URLField()
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default="")
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


class CloudinaryVideoSerializer(serializers.Serializer):
    """Upload/register a Cloudinary video."""
    lesson_id = serializers.UUIDField()
    title = serializers.CharField(max_length=300)
    cloudinary_public_id = serializers.CharField(max_length=300)
    cloudinary_url = serializers.URLField()
    description = serializers.CharField(required=False, default="")
    duration_seconds = serializers.IntegerField(required=False, default=0)
    thumbnail = serializers.URLField(required=False, default="")
    order = serializers.IntegerField(required=False, default=0)
    is_preview = serializers.BooleanField(required=False, default=False)


class S3VideoSerializer(serializers.Serializer):
    """Register an AWS S3 video."""
    lesson_id = serializers.UUIDField()
    title = serializers.CharField(max_length=300)
    s3_key = serializers.CharField(max_length=500)
    s3_bucket = serializers.CharField(max_length=200)
    s3_url = serializers.URLField()
    description = serializers.CharField(required=False, default="")
    duration_seconds = serializers.IntegerField(required=False, default=0)
    thumbnail = serializers.URLField(required=False, default="")
    order = serializers.IntegerField(required=False, default=0)
    is_preview = serializers.BooleanField(required=False, default=False)
