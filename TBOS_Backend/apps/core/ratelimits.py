"""Rate limiting helpers for sensitive endpoints."""

from django_ratelimit.decorators import ratelimit
from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


def ratelimit_auth(func):
    """Rate limit authentication endpoints: 10 requests/minute per IP."""
    return ratelimit(key="ip", rate="10/m", method="POST", block=True)(func)


def ratelimit_quiz_submit(func):
    """Rate limit quiz submissions: 30 requests/minute per user."""
    return ratelimit(key="user", rate="30/m", method="POST", block=True)(func)


def ratelimit_video_import(func):
    """Rate limit video imports: 5 requests/minute per user."""
    return ratelimit(key="user", rate="5/m", method="POST", block=True)(func)
