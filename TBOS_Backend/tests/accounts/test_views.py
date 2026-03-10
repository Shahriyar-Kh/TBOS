import pytest
from rest_framework import status


@pytest.mark.django_db
class TestRegisterEndpoint:
    def test_register_student(self, api_client):
        data = {
            "email": "newuser@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
            "role": "student",
        }
        response = api_client.post("/api/v1/accounts/register/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_register_password_mismatch(self, api_client):
        data = {
            "email": "newuser2@test.com",
            "password": "StrongPass123!",
            "password_confirm": "WrongPass456!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post("/api/v1/accounts/register/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
