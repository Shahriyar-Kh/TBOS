import asyncio

import pytest
from channels.routing import URLRouter
from channels.layers import get_channel_layer
from channels.testing.websocket import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.analytics.routing import websocket_urlpatterns
from apps.analytics.services.realtime_service import student_group
from apps.core.websocket_auth import JwtAuthMiddlewareStack
from tests.factories import CourseFactory, EnrollmentFactory, InstructorFactory, UserFactory


TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "analytics-ws-tests",
    }
}

WS_APPLICATION = JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns))


def access_token_for_user(user):
    return str(RefreshToken.for_user(user).access_token)


def run(coro):
    return asyncio.run(coro)


@pytest.mark.django_db(transaction=True)
class TestAnalyticsWebSocket:
    @pytest.fixture(autouse=True)
    def _configure_settings(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        settings.CACHES = TEST_CACHES
        settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

    def test_websocket_requires_jwt_token(self):
        async def scenario():
            communicator = WebsocketCommunicator(WS_APPLICATION, "/ws/analytics/dashboard/")
            connected, close_code = await communicator.connect()
            await communicator.disconnect()
            return connected, close_code

        connected, close_code = run(scenario())

        assert connected is False
        assert close_code in (4401, 1000)

    def test_student_dashboard_socket_connects_and_responds_to_ping(self):
        student = UserFactory(role="student")
        token = access_token_for_user(student)

        async def scenario():
            communicator = WebsocketCommunicator(
                WS_APPLICATION,
                f"/ws/analytics/dashboard/?token={token}",
            )
            connected, _ = await communicator.connect()
            initial = await communicator.receive_json_from(timeout=10)
            await communicator.send_json_to({"type": "ping"})
            message = await communicator.receive_json_from(timeout=5)
            await communicator.disconnect()
            return connected, initial, message

        connected, initial, message = run(scenario())

        assert connected is True
        assert initial["success"] is True
        assert "overview" in initial["data"]
        assert message["success"] is True
        assert message["message"] == "pong"

    def test_instructor_cannot_join_course_socket_for_other_instructor(self):
        owner = InstructorFactory()
        intruder = InstructorFactory()
        course = CourseFactory(instructor=owner, status="published")
        token = access_token_for_user(intruder)

        async def scenario():
            communicator = WebsocketCommunicator(
                WS_APPLICATION,
                f"/ws/analytics/course/{course.id}/?token={token}",
            )
            connected, close_code = await communicator.connect()
            await communicator.disconnect()
            return connected, close_code

        connected, close_code = run(scenario())

        assert connected is False
        assert close_code in (4403, 1000)

    def test_student_receives_realtime_dashboard_update_event(self):
        student = UserFactory(role="student")
        course = CourseFactory(status="published")
        EnrollmentFactory(student=student, course=course, is_active=True)
        token = access_token_for_user(student)

        async def scenario():
            communicator = WebsocketCommunicator(
                WS_APPLICATION,
                f"/ws/analytics/dashboard/?token={token}",
            )
            connected, _ = await communicator.connect()
            initial = await communicator.receive_json_from(timeout=10)

            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                student_group(student.id),
                {
                    "type": "dashboard.update",
                    "event": "student_dashboard_updated",
                    "data": {"message": "realtime-refresh", "courses_enrolled": 1},
                },
            )
            update = await communicator.receive_json_from(timeout=5)
            await communicator.disconnect()
            return connected, initial, update

        connected, initial, update = run(scenario())

        assert connected is True
        assert initial["success"] is True
        assert update["success"] is True
        assert update["message"] == "student_dashboard_updated"
        assert update["data"]["message"] == "realtime-refresh"
