import uuid

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from apps.accounts.models import Profile, User
from tests.factories import ProfileFactory, UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation_with_email_and_password(self):
        user = UserFactory(email="model-user@example.com")

        assert user.email == "model-user@example.com"
        assert user.check_password("StrongPass123!") is True
        assert user.password != "StrongPass123!"

    def test_email_must_be_unique(self):
        UserFactory(email="unique@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="unique@example.com")

    def test_role_field_accepts_only_valid_roles(self):
        user = UserFactory.build(role="invalid-role")

        with pytest.raises(DjangoValidationError):
            user.full_clean()

    def test_default_role_is_student(self):
        user = UserFactory(role=User.Role.STUDENT)

        assert user.role == User.Role.STUDENT

    def test_uuid_primary_key_is_generated(self):
        user = UserFactory()

        assert isinstance(user.id, uuid.UUID)


@pytest.mark.django_db
class TestProfileModel:
    def test_profile_automatically_created_for_user(self):
        user = UserFactory()

        assert hasattr(user, "profile")
        assert isinstance(user.profile, Profile)

    def test_profile_linked_correctly_to_user(self):
        profile = ProfileFactory()

        assert profile.user.profile.id == profile.id

    def test_profile_update_works(self):
        profile = ProfileFactory(bio="Original bio")

        profile.bio = "Updated bio"
        profile.skills = ["Django", "Pytest"]
        profile.save()
        profile.refresh_from_db()

        assert profile.bio == "Updated bio"
        assert profile.skills == ["Django", "Pytest"]

    def test_profile_field_validation_works(self):
        profile = ProfileFactory.build(phone_number="bad-phone", website="not-a-url")

        with pytest.raises(DjangoValidationError):
            profile.full_clean()
