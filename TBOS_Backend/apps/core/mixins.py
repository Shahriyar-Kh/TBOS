"""
Reusable mixins for views and serializers.
"""

from rest_framework.response import Response
from rest_framework import status


class APIResponseMixin:
    """Mixin that wraps DRF responses in a standard envelope."""

    def success_response(self, data=None, message="", status_code=status.HTTP_200_OK):
        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
            },
            status=status_code,
        )

    def created_response(self, data=None, message="Created successfully."):
        return self.success_response(data, message, status.HTTP_201_CREATED)

    def error_response(self, errors=None, message="", status_code=status.HTTP_400_BAD_REQUEST):
        return Response(
            {
                "success": False,
                "message": message,
                "errors": errors,
            },
            status=status_code,
        )


class MultiSerializerMixin:
    """
    Mixin to use different serializers for different actions
    in a ViewSet.

    Usage:
        serializer_classes = {
            "list": MyListSerializer,
            "create": MyCreateSerializer,
            "default": MyDefaultSerializer,
        }
    """

    serializer_classes: dict = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(
            self.action,
            self.serializer_classes.get("default", super().get_serializer_class()),
        )
