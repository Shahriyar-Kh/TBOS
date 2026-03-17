from rest_framework_simplejwt.tokens import RefreshToken


def auth_headers_for(user):
    token = str(RefreshToken.for_user(user).access_token)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def assert_api_success_envelope(response):
    assert "success" in response.data
    assert "message" in response.data
    assert response.data["success"] is True


def assert_api_error_envelope(response):
    assert "success" in response.data
    assert "message" in response.data
    assert response.data["success"] is False
