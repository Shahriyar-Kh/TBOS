import pytest
from rest_framework.test import APIRequestFactory

from apps.core.permissions import IsAdmin, IsInstructor, IsOwner, IsOwnerOrAdmin, IsStudent
from tests.factories import AdminFactory, InstructorFactory, ProfileFactory, UserFactory


class DummyView:
    pass


@pytest.mark.django_db
class TestAccountPermissions:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.view = DummyView()

    def test_is_admin_permission(self):
        request = self.factory.get("/api/v1/admin/users/")
        request.user = AdminFactory()

        assert IsAdmin().has_permission(request, self.view) is True

    def test_is_instructor_permission(self):
        request = self.factory.get("/api/v1/instructor/")
        request.user = InstructorFactory()

        assert IsInstructor().has_permission(request, self.view) is True

    def test_student_cannot_access_instructor_permission(self):
        request = self.factory.get("/api/v1/instructor/")
        request.user = UserFactory()

        assert IsInstructor().has_permission(request, self.view) is False

    def test_is_student_permission(self):
        request = self.factory.get("/api/v1/student/")
        request.user = UserFactory()

        assert IsStudent().has_permission(request, self.view) is True

    def test_is_owner_permission(self):
        user = UserFactory()
        profile = ProfileFactory(user=user)
        request = self.factory.get("/api/v1/auth/profile/")
        request.user = user

        assert IsOwner().has_object_permission(request, self.view, profile) is True

    def test_is_owner_or_admin_permission(self):
        other_user = UserFactory()
        profile = ProfileFactory(user=other_user)
        request = self.factory.get("/api/v1/auth/profile/")
        request.user = AdminFactory()

        assert IsOwnerOrAdmin().has_object_permission(request, self.view, profile) is True