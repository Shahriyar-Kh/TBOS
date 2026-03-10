from django.urls import path

from apps.ai_tools import views

urlpatterns = [
    path("generate-quiz/", views.AIQuizGenerateView.as_view(), name="ai-generate-quiz"),
    path(
        "generate-quiz/<uuid:pk>/status/",
        views.AIQuizStatusView.as_view(),
        name="ai-quiz-status",
    ),
    path("suggest/", views.AISuggestView.as_view(), name="ai-suggest"),
    path("suggestions/", views.AISuggestionHistoryView.as_view(), name="ai-suggestions"),
]
