"""Tests for course-related permissions."""
import pytest

from apps.core.permissions import IsAdmin, IsAdminOrInstructor, IsInstructor, IsOwnerInstructor
from apps.courses.models import Category, Course


@pytest.fixture
def category(db):
    return Category.objects.create(name="Perm Test Cat")


@pytest.fixture
def course(db, instructor_user, category):
    return Course.objects.create(
        title="Permission Test Course",
        description="Testing permissions",
        instructor=instructor_user,
        category=category,
        price="0",
    )


class TestIsOwnerInstructor:
    """IsOwnerInstructor permission: view-level requires instructor/admin role;
    object-level requires course ownership or admin."""

    def _make_request(self, user):
        from unittest.mock import MagicMock
        request = MagicMock()
        request.user = user
        return request

    def test_instructor_has_view_permission(self, instructor_user):
        perm = IsOwnerInstructor()
        request = self._make_request(instructor_user)
        assert perm.has_permission(request, None) is True

    def test_admin_has_view_permission(self, admin_user):
        perm = IsOwnerInstructor()
        request = self._make_request(admin_user)
        assert perm.has_permission(request, None) is True

    def test_student_has_no_view_permission(self, student_user):
        perm = IsOwnerInstructor()
        request = self._make_request(student_user)
        assert perm.has_permission(request, None) is False

    def test_instructor_owns_course_has_object_permission(
        self, instructor_user, course
    ):
        perm = IsOwnerInstructor()
        request = self._make_request(instructor_user)
        assert perm.has_object_permission(request, None, course) is True

    def test_instructor_does_not_own_course(self, db, course):
        from tests.factories import InstructorFactory
        other = InstructorFactory()
        perm = IsOwnerInstructor()
        request = self._make_request(other)
        assert perm.has_object_permission(request, None, course) is False

    def test_admin_can_access_any_course(self, admin_user, course):
        perm = IsOwnerInstructor()
        request = self._make_request(admin_user)
        assert perm.has_object_permission(request, None, course) is True


class TestIsAdminPermission:
    def _make_request(self, user):
        from unittest.mock import MagicMock
        request = MagicMock()
        request.user = user
        return request

    def test_admin_has_permission(self, admin_user):
        perm = IsAdmin()
        request = self._make_request(admin_user)
        assert perm.has_permission(request, None) is True

    def test_instructor_has_no_admin_permission(self, instructor_user):
        perm = IsAdmin()
        request = self._make_request(instructor_user)
        assert perm.has_permission(request, None) is False

    def test_student_has_no_admin_permission(self, student_user):
        perm = IsAdmin()
        request = self._make_request(student_user)
        assert perm.has_permission(request, None) is False
