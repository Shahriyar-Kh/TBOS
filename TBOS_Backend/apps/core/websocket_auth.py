from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtAuthMiddleware(BaseMiddleware):
    """Authenticate websocket connections using JWT passed as ?token=..."""

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        query_params = parse_qs(scope.get("query_string", b"").decode())
        token = query_params.get("token", [None])[0]
        if token:
            scope["user"] = await self._get_user(token)

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _get_user(self, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            return jwt_auth.get_user(validated_token)
        except Exception:
            return AnonymousUser()


def JwtAuthMiddlewareStack(inner):
    return AuthMiddlewareStack(JwtAuthMiddleware(inner))
