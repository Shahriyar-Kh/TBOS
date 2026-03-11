import io

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import AdminFactory, InstructorFactory, ProfileFactory, UserFactory


@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"
    settings.GOOGLE_OAUTH_CLIENT_SECRET = "test-google-client-secret"
    return settings.MEDIA_ROOT


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def student_user(db):
    return UserFactory()


@pytest.fixture
def instructor_user(db):
    return InstructorFactory()


@pytest.fixture
def admin_user(db):
    return AdminFactory()


@pytest.fixture
def student_profile(student_user):
    return ProfileFactory(user=student_user)


@pytest.fixture
def instructor_profile(instructor_user):
    return ProfileFactory(user=instructor_user)


@pytest.fixture
def admin_profile(admin_user):
    return ProfileFactory(user=admin_user)


@pytest.fixture
def access_token_for_user():
    def make_token(user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    return make_token


@pytest.fixture
def auth_client(api_client, student_user, access_token_for_user):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(student_user)}")
    return api_client


@pytest.fixture
def instructor_client(api_client, instructor_user, access_token_for_user):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user, access_token_for_user):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(admin_user)}")
    return api_client


def _image_file(name, size=(100, 100), image_format="PNG", content_type="image/png"):
    buffer = io.BytesIO()
    image = Image.new("RGB", size=size, color="blue")
    image.save(buffer, format=image_format)
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@pytest.fixture
def avatar_file():
    return _image_file("avatar.png")


@pytest.fixture
def large_avatar_file(monkeypatch):
    return _image_file(
        "large-avatar.bmp",
        size=(2200, 2200),
        image_format="BMP",
        content_type="image/bmp",
    )
