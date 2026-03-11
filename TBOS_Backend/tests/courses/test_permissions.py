<<<<<<< HEAD
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
=======
from unittest.mock import MagicMock

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.core.permissions import (
    IsAdmin,
    IsAdminOrInstructor,
    IsEnrolledOrInstructor,
    IsInstructor,
    IsOwner,
    IsOwnerOrAdmin,
    IsStudent,
)
from tests.factories import AdminFactory, InstructorFactory, UserFactory


def make_request(user=None, method="GET"):
    factory = APIRequestFactory()
    request = getattr(factory, method.lower())("/")
    request.user = user or MagicMock(is_authenticated=False)
    return request


@pytest.mark.django_db
class TestIsAdminPermission:
    def test_admin_has_permission(self):
        admin = AdminFactory()
        request = make_request(admin)

        assert IsAdmin().has_permission(request, None) is True

    def test_instructor_has_no_permission(self):
        instructor = InstructorFactory()
        request = make_request(instructor)

        assert IsAdmin().has_permission(request, None) is False

    def test_student_has_no_permission(self):
        student = UserFactory()
        request = make_request(student)

        assert IsAdmin().has_permission(request, None) is False

    def test_unauthenticated_has_no_permission(self):
        user = MagicMock(is_authenticated=False, role="admin")
        request = make_request(user)

        assert IsAdmin().has_permission(request, None) is False


@pytest.mark.django_db
class TestIsInstructorPermission:
    def test_instructor_has_permission(self):
        instructor = InstructorFactory()
        request = make_request(instructor)

        assert IsInstructor().has_permission(request, None) is True

    def test_admin_has_no_permission(self):
        admin = AdminFactory()
        request = make_request(admin)

        assert IsInstructor().has_permission(request, None) is False

    def test_student_has_no_permission(self):
        student = UserFactory()
        request = make_request(student)

        assert IsInstructor().has_permission(request, None) is False


@pytest.mark.django_db
class TestIsStudentPermission:
    def test_student_has_permission(self):
        student = UserFactory()
        request = make_request(student)

        assert IsStudent().has_permission(request, None) is True

    def test_instructor_has_no_permission(self):
        instructor = InstructorFactory()
        request = make_request(instructor)

        assert IsStudent().has_permission(request, None) is False

    def test_admin_has_no_permission(self):
        admin = AdminFactory()
        request = make_request(admin)

        assert IsStudent().has_permission(request, None) is False


@pytest.mark.django_db
class TestIsAdminOrInstructorPermission:
    def test_admin_has_permission(self):
        admin = AdminFactory()
        request = make_request(admin)

        assert IsAdminOrInstructor().has_permission(request, None) is True

    def test_instructor_has_permission(self):
        instructor = InstructorFactory()
        request = make_request(instructor)

        assert IsAdminOrInstructor().has_permission(request, None) is True

    def test_student_has_no_permission(self):
        student = UserFactory()
        request = make_request(student)

        assert IsAdminOrInstructor().has_permission(request, None) is False

    def test_unauthenticated_has_no_permission(self):
        user = MagicMock(is_authenticated=False, role="instructor")
        request = make_request(user)

        assert IsAdminOrInstructor().has_permission(request, None) is False


@pytest.mark.django_db
class TestIsOwnerPermission:
    def test_owner_has_object_permission_via_user_attr(self):
        user = UserFactory()
        obj = MagicMock(user=user)
        request = make_request(user)

        assert IsOwner().has_object_permission(request, None, obj) is True

    def test_non_owner_has_no_object_permission_via_user_attr(self):
        owner = UserFactory()
        other = UserFactory()
        obj = MagicMock(user=owner)
        request = make_request(other)
        del obj.student
        del obj.instructor

        assert IsOwner().has_object_permission(request, None, obj) is False

    def test_owner_has_permission_via_instructor_attr(self):
        instructor = InstructorFactory()
        obj = MagicMock(spec=["instructor"])
        obj.instructor = instructor
        request = make_request(instructor)

        assert IsOwner().has_object_permission(request, None, obj) is True

    def test_non_owner_has_no_permission_via_instructor_attr(self):
        instructor = InstructorFactory()
        other_instructor = InstructorFactory()
        obj = MagicMock(spec=["instructor"])
        obj.instructor = instructor
        request = make_request(other_instructor)

        assert IsOwner().has_object_permission(request, None, obj) is False


@pytest.mark.django_db
class TestIsOwnerOrAdminPermission:
    def test_admin_has_object_permission(self):
        admin = AdminFactory()
        obj = MagicMock()
        request = make_request(admin)

        assert IsOwnerOrAdmin().has_object_permission(request, None, obj) is True

    def test_owner_has_object_permission(self):
        user = UserFactory()
        obj = MagicMock(user=user)
        request = make_request(user)

        assert IsOwnerOrAdmin().has_object_permission(request, None, obj) is True

    def test_non_owner_non_admin_has_no_permission(self):
        owner = UserFactory()
        other = UserFactory()
        obj = MagicMock(user=owner)
        request = make_request(other)

        assert IsOwnerOrAdmin().has_object_permission(request, None, obj) is False


@pytest.mark.django_db
class TestIsEnrolledOrInstructorPermission:
    def test_admin_has_object_permission(self):
        admin = AdminFactory()
        obj = MagicMock()
        request = make_request(admin)

        assert IsEnrolledOrInstructor().has_object_permission(request, None, obj) is True

    def test_course_instructor_has_object_permission(self):
        instructor = InstructorFactory()
        course = MagicMock()
        course.instructor = instructor
        course.enrollments = MagicMock()
        obj = MagicMock(course=course)
        request = make_request(instructor)

        assert IsEnrolledOrInstructor().has_object_permission(request, None, obj) is True

    def test_enrolled_student_has_object_permission(self):
        student = UserFactory()
        course = MagicMock()
        course.instructor = InstructorFactory()
        enrollment_qs = MagicMock()
        enrollment_qs.exists.return_value = True
        course.enrollments.filter.return_value = enrollment_qs
        obj = MagicMock(course=course)
        request = make_request(student)

        assert IsEnrolledOrInstructor().has_object_permission(request, None, obj) is True

    def test_non_enrolled_student_has_no_permission(self):
        student = UserFactory()
        course = MagicMock()
        course.instructor = InstructorFactory()
        enrollment_qs = MagicMock()
        enrollment_qs.exists.return_value = False
        course.enrollments.filter.return_value = enrollment_qs
        obj = MagicMock(course=course)
        request = make_request(student)

        assert IsEnrolledOrInstructor().has_object_permission(request, None, obj) is False

    def test_non_instructor_non_student_has_no_permission(self):
        other_instructor = InstructorFactory()
        course_instructor = InstructorFactory()
        course = MagicMock()
        course.instructor = course_instructor
        course.enrollments = MagicMock()
        obj = MagicMock(course=course)
        request = make_request(other_instructor)

        assert IsEnrolledOrInstructor().has_object_permission(request, None, obj) is False


# ──────────────────────────────────────────────
# Role-based access via API endpoints
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestRoleBasedAccessViaAPI:
    def test_student_can_access_public_course_list(self, auth_client):
        response = auth_client.get("/api/v1/courses/")

        assert response.status_code == 200

    def test_instructor_can_access_instructor_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/courses/instructor/courses/")

        assert response.status_code == 200

    def test_student_cannot_access_instructor_create(self, auth_client):
        from tests.factories import CategoryFactory

        category = CategoryFactory(name="Role Test Cat")
        response = auth_client.post(
            "/api/v1/courses/instructor/courses/",
            {
                "title": "Unauthorized",
                "description": "No",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_access_instructor_endpoint(self, api_client):
        response = api_client.get("/api/v1/courses/instructor/courses/")

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    def test_admin_can_manage_categories(self, admin_client):
        response = admin_client.get("/api/v1/courses/admin/categories/")

        assert response.status_code == status.HTTP_200_OK

    def test_student_cannot_manage_categories(self, auth_client):
        response = auth_client.get("/api/v1/courses/admin/categories/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_manage_admin_categories(self, instructor_client):
        response = instructor_client.get("/api/v1/courses/admin/categories/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
>>>>>>> 36e9d9d1ebb34bf8b78a481d28bf7cf2ca6f757e
