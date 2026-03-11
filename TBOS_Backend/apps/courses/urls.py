from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.courses import views

router = DefaultRouter()
router.register(
    r"instructor/courses",
    views.InstructorCourseViewSet,
    basename="instructor-courses",
)
router.register(r"admin/courses", views.AdminCourseViewSet, basename="admin-courses")
router.register(r"admin/categories", views.AdminCategoryViewSet, basename="admin-categories")
router.register(r"admin/levels", views.AdminLevelViewSet, basename="admin-levels")
router.register(r"admin/languages", views.AdminLanguageViewSet, basename="admin-languages")

urlpatterns = [
    path("", views.PublicCourseListView.as_view(), name="course-list"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("levels/", views.LevelListView.as_view(), name="level-list"),
    path("languages/", views.LanguageListView.as_view(), name="language-list"),
    path("", include(router.urls)),
    # Slug-based detail must come after the router includes to avoid conflicts
    path("<slug:slug>/", views.PublicCourseDetailView.as_view(), name="course-detail"),
]
