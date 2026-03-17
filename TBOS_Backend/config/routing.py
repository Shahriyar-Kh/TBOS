from django.urls import path

from apps.analytics.routing import websocket_urlpatterns as analytics_ws


websocket_urlpatterns = [
    *analytics_ws,
]
