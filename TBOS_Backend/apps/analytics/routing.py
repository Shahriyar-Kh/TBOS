from django.urls import re_path

from apps.analytics.consumers import AnalyticsDashboardConsumer


websocket_urlpatterns = [
    re_path(r"ws/analytics/dashboard/$", AnalyticsDashboardConsumer.as_asgi()),
    re_path(r"ws/analytics/course/(?P<course_id>[0-9a-f\-]+)/$", AnalyticsDashboardConsumer.as_asgi()),
]
