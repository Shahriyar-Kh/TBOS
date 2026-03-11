from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.courses import views
from apps.lessons.views import CourseCurriculumView

# Use SimpleRouter to avoid generating an authenticated API root view
# that would shadow the public course list endpoint.
router = SimpleRouter()
router.register(
    r"instructor/courses",
    views.InstructorCourseViewSet,
    basename="instructor-courses",
)
router.register(
    r"admin/courses",
    views.AdminCourseViewSet,
    basename="admin-courses",
)
router.register(r"admin/categories", views.AdminCategoryViewSet, basename="admin-categories")
router.register(r"admin/levels", views.AdminLevelViewSet, basename="admin-levels")
router.register(r"admin/languages", views.AdminLanguageViewSet, basename="admin-languages")

urlpatterns = [
    # Public read-only endpoints  (no auth required)
    path("", views.PublicCourseListView.as_view(), name="course-list"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("levels/", views.LevelListView.as_view(), name="level-list"),
    path("languages/", views.LanguageListView.as_view(), name="language-list"),
    # Instructor + Admin router-generated URLs
    path("", include(router.urls)),
    # Public course detail must come AFTER router URLs to avoid
    # capturing slug-like paths that belong to instructor/admin routes.
    path("<slug:slug>/", views.PublicCourseDetailView.as_view(), name="course-detail"),
    # Course curriculum endpoint
    path(
        "<slug:slug>/curriculum/",
        CourseCurriculumView.as_view({"get": "retrieve"}),
        name="course-curriculum",
    ),
]
