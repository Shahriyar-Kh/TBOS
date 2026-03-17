import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder

from apps.analytics.services.analytics_service import (
    get_admin_dashboard,
    get_instructor_dashboard,
    get_student_dashboard,
)
from apps.analytics.services.realtime_service import (
    admin_group,
    course_group,
    instructor_group,
    student_group,
)
from apps.courses.models import Course


class AnalyticsDashboardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.joined_groups = []

        if user.role == "student":
            await self._join_group(student_group(user.id))
            payload = await self._student_snapshot(user)
        elif user.role == "instructor":
            await self._join_group(instructor_group(user.id))
            payload = await self._instructor_snapshot(user)
        elif user.role == "admin":
            await self._join_group(admin_group())
            payload = await self._admin_snapshot()
        else:
            await self.close(code=4403)
            return

        course_id = self.scope.get("url_route", {}).get("kwargs", {}).get("course_id")
        if course_id:
            allowed = await self._can_access_course(user, course_id)
            if not allowed:
                await self.close(code=4403)
                return
            await self._join_group(course_group(course_id))

        await self.accept()
        await self.send_json(
            {
                "success": True,
                "message": "WebSocket connected.",
                "data": self._to_jsonable(payload),
            }
        )

    async def disconnect(self, close_code):
        for group_name in getattr(self, "joined_groups", []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"success": True, "message": "pong", "data": {}})

    async def dashboard_update(self, event):
        await self.send_json(
            {
                "success": True,
                "message": event.get("event", "dashboard_update"),
                "data": self._to_jsonable(event.get("data", {})),
            }
        )

    def _to_jsonable(self, payload):
        return json.loads(json.dumps(payload, cls=DjangoJSONEncoder))

    async def _join_group(self, group_name):
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.joined_groups.append(group_name)

    @database_sync_to_async
    def _student_snapshot(self, user):
        return get_student_dashboard(user)

    @database_sync_to_async
    def _instructor_snapshot(self, user):
        return get_instructor_dashboard(user)

    @database_sync_to_async
    def _admin_snapshot(self):
        return get_admin_dashboard()

    @database_sync_to_async
    def _can_access_course(self, user, course_id):
        try:
            course = Course.objects.only("id", "instructor_id").get(id=course_id)
        except Course.DoesNotExist:
            return False

        if user.role == "admin":
            return True
        if user.role == "instructor":
            return course.instructor_id == user.id
        return False
