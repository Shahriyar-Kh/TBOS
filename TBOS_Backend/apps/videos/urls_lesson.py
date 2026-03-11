"""
Lesson-nested video URL.

Mounted at /api/v1/lessons/<lesson_pk>/video/ by apps.lessons.urls.
"""
from django.urls import path

from apps.videos.views import LessonVideoView

urlpatterns = [
    path(
        "",
        LessonVideoView.as_view({"get": "retrieve"}),
        name="lesson-video-retrieve",
    ),
]
