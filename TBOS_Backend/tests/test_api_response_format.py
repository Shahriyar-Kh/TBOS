import pytest


@pytest.mark.django_db
class TestAPIResponseFormat:
    @pytest.mark.parametrize(
        "url",
        [
            "/api/v1/courses/",
            "/api/v1/reviews/public/",
        ],
    )
    def test_public_endpoints_return_standard_envelope(self, api_client, url):
        response = api_client.get(url)
        assert response.status_code == 200
        if "results" in response.data:
            assert "count" in response.data
            assert "next" in response.data
            assert "previous" in response.data
        else:
            assert "success" in response.data
            assert "message" in response.data

    def test_protected_endpoint_unauthorized_returns_standard_error(self, api_client):
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == 401
        assert "success" in response.data
        assert response.data["success"] is False
