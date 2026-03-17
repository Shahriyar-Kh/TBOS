import pytest

from apps.enrollments.serializers import VideoProgressUpdateSerializer


@pytest.mark.django_db
class TestEnrollmentSerializers:
    def test_video_progress_update_serializer_accepts_non_negative_values(self):
        serializer = VideoProgressUpdateSerializer(
            data={
                "video_id": "a8d7ad0f-f198-4dc4-9a7e-d0470de95df8",
                "watch_time_seconds": 30,
                "last_position_seconds": 20,
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_video_progress_update_serializer_rejects_negative_values(self):
        serializer = VideoProgressUpdateSerializer(
            data={
                "video_id": "a8d7ad0f-f198-4dc4-9a7e-d0470de95df8",
                "watch_time_seconds": -1,
                "last_position_seconds": 0,
            }
        )
        assert not serializer.is_valid()
        assert "watch_time_seconds" in serializer.errors
