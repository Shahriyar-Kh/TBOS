from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "message": _extract_message(response.data),
            "errors": response.data,
            "status_code": response.status_code,
        }
    else:
        response = Response(
            {
                "success": False,
                "message": "An unexpected error occurred.",
                "errors": {"detail": "An unexpected error occurred."},
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data):
    """Extract a human-readable message from DRF error data."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
        first_key = next(iter(data), None)
        if first_key:
            val = data[first_key]
            if isinstance(val, list) and val:
                return str(val[0])
            return str(val)
    if isinstance(data, list) and data:
        return str(data[0])
    return "An error occurred."


def api_success(data=None, message="", status_code=status.HTTP_200_OK):
    """Standard success response helper."""
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def api_error(errors=None, message="", status_code=status.HTTP_400_BAD_REQUEST):
    """Standard error response helper."""
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors,
        },
        status=status_code,
    )
