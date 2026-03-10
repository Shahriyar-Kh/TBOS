"""
conftest.py — shared pytest fixtures for TBOS tests.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@test.com",
        password="testpass123",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        email="instructor@test.com",
        password="testpass123",
        first_name="Instructor",
        last_name="User",
        role="instructor",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student@test.com",
        password="testpass123",
        first_name="Student",
        last_name="User",
        role="student",
    )


@pytest.fixture
def auth_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def instructor_client(api_client, instructor_user):
    api_client.force_authenticate(user=instructor_user)
    return api_client
