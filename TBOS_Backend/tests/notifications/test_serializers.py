import pytest

from apps.notifications.serializers import BroadcastNotificationSerializer


@pytest.mark.django_db
class TestNotificationSerializers:
    def test_broadcast_notification_serializer_validates_required_fields(self):
        serializer = BroadcastNotificationSerializer(data={"title": "System", "message": "Maintenance"})
        assert serializer.is_valid(), serializer.errors

    def test_broadcast_notification_serializer_rejects_missing_message(self):
        serializer = BroadcastNotificationSerializer(data={"title": "System"})
        assert not serializer.is_valid()
        assert "message" in serializer.errors
