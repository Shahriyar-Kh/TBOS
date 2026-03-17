from rest_framework import serializers

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, inline_serializer


ROLE_ACCESS_GUIDE = (
    "Role-based access:\n"
    "- Admin: platform-wide management and reporting endpoints.\n"
    "- Instructor: course-authoring, grading, quiz authoring, and instructor analytics.\n"
    "- Student: course consumption, submissions, quiz attempts, payments, and progress tracking."
)

AUTH_GUIDE = (
    "JWT Bearer authentication is used for protected endpoints. "
    "Include the access token in the Authorization header as: Bearer <token>."
)

AUTH_RATE_LIMIT_NOTE = "Authentication endpoints are rate-limited to 10 requests per minute per IP address."
QUIZ_RATE_LIMIT_NOTE = "Quiz answer submission and final submission are rate-limited to 30 POST requests per minute per user."
VIDEO_IMPORT_RATE_LIMIT_NOTE = "Video import endpoints are rate-limited to 5 POST requests per minute per user."

USER_EXAMPLE = {
    "id": "7f1d6d54-0c9a-4a1f-b819-4e0be08d8a11",
    "email": "amina.student@tbos.dev",
    "username": "amina.student",
    "first_name": "Amina",
    "last_name": "Yusuf",
    "role": "student",
    "is_verified": True,
    "google_account": False,
    "is_active": True,
    "date_joined": "2026-03-01T09:30:00Z",
    "last_login": "2026-03-17T08:15:00Z",
    "profile": {
        "id": "d3f65c7d-d229-4234-b2bc-6de6dff4fcdb",
        "avatar": "https://res.cloudinary.com/tbos/image/upload/v1/avatars/amina.png",
        "bio": "Frontend learner focusing on React and TypeScript.",
        "headline": "Aspiring Frontend Engineer",
        "country": "Nigeria",
        "city": "Lagos",
        "timezone": "Africa/Lagos",
        "phone_number": "+2348000000000",
        "website": "https://aminayusuf.dev",
        "linkedin": "https://linkedin.com/in/aminayusuf",
        "github": "https://github.com/aminayusuf",
        "twitter": "https://x.com/aminayusuf",
        "skills": "React, TypeScript, Tailwind CSS",
        "education": "B.Sc. Computer Science",
        "experience": "2 years internship experience",
        "profile_visibility": "public",
        "date_created": "2026-03-01T09:30:00Z",
        "date_updated": "2026-03-17T08:15:00Z",
    },
}

COURSE_EXAMPLE = {
    "id": "7aafda24-f71d-4f7f-87d1-f2ea189ba5c4",
    "title": "Modern Django for Product Teams",
    "slug": "modern-django-for-product-teams",
    "subtitle": "Build and operate production-ready Django services.",
    "thumbnail": "https://res.cloudinary.com/tbos/image/upload/v1/courses/django-thumb.jpg",
    "price": "149.00",
    "effective_price": "99.00",
    "is_free": False,
    "category": {
        "id": "d7637e3d-92f0-4508-bba3-e27863bce58d",
        "name": "Backend Development",
        "icon": "server",
        "slug": "backend-development",
    },
    "level": {"id": "9c935c26-cc6d-49d4-bf63-c71cf6dba11c", "name": "Intermediate"},
    "language": {"id": "00432bf4-6a3f-4b52-9a1c-64db5b0a4adb", "name": "English"},
    "instructor_name": "John Builder",
    "average_rating": "4.80",
    "rating_count": 128,
    "total_enrollments": 1540,
    "duration_hours": "18.50",
    "total_lessons": 42,
}

LESSON_EXAMPLE = {
    "id": "a5f08d91-c5d5-4add-a4a5-31cb14985d0e",
    "title": "Designing your Django service boundaries",
    "description": "Split API, services, and persistence layers cleanly.",
    "order": 3,
    "is_preview": True,
}

VIDEO_EXAMPLE = {
    "id": "f3d8b6c2-d8f8-4ef0-a2f4-7cbd72b309d4",
    "title": "Deploying Django on Render and PostgreSQL",
    "order": 1,
    "source_type": "youtube",
    "thumbnail": "https://img.youtube.com/vi/demo/maxresdefault.jpg",
    "duration_seconds": 845,
    "is_preview": True,
    "playback_url": "https://www.youtube.com/watch?v=demo",
}

QUIZ_EXAMPLE = {
    "id": "7c4d1963-2e77-4e37-a8aa-8efb4a547f4c",
    "title": "Django ORM Foundations",
    "instructions": "Select the best answer for each question.",
    "max_attempts": 3,
    "passing_score": 70,
    "time_limit_minutes": 20,
    "is_active": True,
}

ASSIGNMENT_EXAMPLE = {
    "id": "346fb31f-6990-4bd0-8798-91bf546882cf",
    "title": "Build a course review API",
    "description": "Implement review submission and moderation endpoints.",
    "submission_type": "file_and_text",
    "due_date": "2026-03-30T23:59:00Z",
    "max_score": 100,
    "max_attempts": 2,
}

REVIEW_EXAMPLE = {
    "id": "ef2ea5bc-1202-4a96-b0ce-c9bc55c46015",
    "rating": 5,
    "review_text": "Very practical course with strong API design examples.",
    "status": "published",
}

PAYMENT_EXAMPLE = {
    "id": "bbf3e5b9-7b26-4294-b4ce-3fa6cc786f6b",
    "order_number": "TBOS-20260317-1024",
    "amount": "99.00",
    "currency": "USD",
    "status": "completed",
    "payment_method": "stripe",
}

CERTIFICATE_EXAMPLE = {
    "id": "a1191afe-ff53-4d34-a0bb-faf6fc52867a",
    "certificate_number": "TBOS-CERT-2026-00041",
    "verification_code": "TBOSVERIFY12345",
    "student_name": "Amina Yusuf",
    "course_title": "Modern Django for Product Teams",
    "issued_at": "2026-03-16T16:45:00Z",
}


def _resolve_serializer(serializer_or_field, many=False):
    if serializer_or_field is None:
        return serializers.JSONField(required=False, allow_null=True)
    if isinstance(serializer_or_field, serializers.BaseSerializer):
        return serializer_or_field
    if isinstance(serializer_or_field, serializers.Field):
        return serializer_or_field
    if isinstance(serializer_or_field, type):
        if issubclass(serializer_or_field, serializers.BaseSerializer):
            return serializer_or_field(many=many)
        if issubclass(serializer_or_field, serializers.Field):
            return serializer_or_field()
    return serializers.JSONField(required=False, allow_null=True)


def success_envelope_serializer(name, data=None, many=False):
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(),
            "data": _resolve_serializer(data, many=many),
        },
    )


def paginated_data_serializer(name, item_serializer):
    return inline_serializer(
        name=name,
        fields={
            "page": serializers.IntegerField(help_text="Current page number."),
            "page_size": serializers.IntegerField(help_text="Requested page size."),
            "total_count": serializers.IntegerField(help_text="Total records across all pages."),
            "count": serializers.IntegerField(help_text="Backward-compatible alias of total_count."),
            "next": serializers.URLField(required=False, allow_null=True),
            "previous": serializers.URLField(required=False, allow_null=True),
            "results": _resolve_serializer(item_serializer, many=True),
        },
    )


def paginated_success_envelope_serializer(name, item_serializer):
    return success_envelope_serializer(
        name=name,
        data=paginated_data_serializer(f"{name}Page", item_serializer),
    )


def error_envelope_serializer(name):
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(default=False),
            "message": serializers.CharField(),
            "errors": serializers.JSONField(required=False, allow_null=True),
            "status_code": serializers.IntegerField(required=False),
        },
    )


BAD_REQUEST_ERROR_SERIALIZER = error_envelope_serializer("BadRequestError")
UNAUTHORIZED_ERROR_SERIALIZER = error_envelope_serializer("UnauthorizedError")
FORBIDDEN_ERROR_SERIALIZER = error_envelope_serializer("ForbiddenError")
NOT_FOUND_ERROR_SERIALIZER = error_envelope_serializer("NotFoundError")
RATE_LIMIT_ERROR_SERIALIZER = error_envelope_serializer("RateLimitError")
SERVER_ERROR_SERIALIZER = error_envelope_serializer("ServerError")


def success_response(name, data=None, *, many=False, description="", examples=None):
    return OpenApiResponse(
        response=success_envelope_serializer(name, data=data, many=many),
        description=description,
        examples=examples or [],
    )


def paginated_response(name, item_serializer, *, description="", examples=None):
    return OpenApiResponse(
        response=paginated_success_envelope_serializer(name, item_serializer),
        description=description,
        examples=examples or [],
    )


def error_response(name, description, example_message, *, status_code, errors=None):
    serializer_mapping = {
        400: BAD_REQUEST_ERROR_SERIALIZER,
        401: UNAUTHORIZED_ERROR_SERIALIZER,
        403: FORBIDDEN_ERROR_SERIALIZER,
        404: NOT_FOUND_ERROR_SERIALIZER,
        429: RATE_LIMIT_ERROR_SERIALIZER,
        500: SERVER_ERROR_SERIALIZER,
    }
    return OpenApiResponse(
        response=serializer_mapping.get(status_code, SERVER_ERROR_SERIALIZER),
        description=description,
        examples=[
            OpenApiExample(
                name=f"{status_code}Error",
                value={
                    "success": False,
                    "message": example_message,
                    "errors": errors or {"detail": example_message},
                    "status_code": status_code,
                },
                response_only=True,
            )
        ],
    )


def standard_error_responses(*codes):
    mapping = {
        400: error_response(
            "BadRequestError",
            "Request validation failed.",
            "Invalid request payload.",
            status_code=400,
            errors={"field": ["This field is required."]},
        ),
        401: error_response(
            "UnauthorizedError",
            "Authentication credentials were missing or invalid.",
            "Authentication credentials were not provided.",
            status_code=401,
        ),
        403: error_response(
            "ForbiddenError",
            "The authenticated user does not have permission to access this resource.",
            "You do not have permission to perform this action.",
            status_code=403,
        ),
        404: error_response(
            "NotFoundError",
            "The requested resource could not be found.",
            "Resource not found.",
            status_code=404,
        ),
        429: error_response(
            "RateLimitError",
            "The client exceeded the configured rate limit.",
            "Request was throttled. Expected available in 60 seconds.",
            status_code=429,
        ),
        500: error_response(
            "ServerError",
            "Unexpected server-side failure.",
            "An unexpected error occurred.",
            status_code=500,
        ),
    }
    return {code: mapping[code] for code in codes}


def success_example(name, message, data, *, status_code=None):
    example = {
        "success": True,
        "message": message,
        "data": data,
    }
    if status_code is not None:
        example["status_code"] = status_code
    return OpenApiExample(name=name, value=example, response_only=True)


PAGE_PARAM = OpenApiParameter(
    name="page",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description="Page number to retrieve.",
)

PAGE_SIZE_PARAM = OpenApiParameter(
    name="page_size",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description="Number of results per page. Maximum 100 unless overridden by the endpoint.",
)

SEARCH_PARAM = OpenApiParameter(
    name="search",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Case-insensitive keyword search.",
)

CATEGORY_PARAM = OpenApiParameter(
    name="category",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Filter by category slug or identifier, depending on the endpoint.",
)

LEVEL_PARAM = OpenApiParameter(
    name="level",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Filter by course level identifier.",
)

LANGUAGE_PARAM = OpenApiParameter(
    name="language",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Filter by language identifier.",
)

SORTING_PARAM = OpenApiParameter(
    name="ordering",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Sort results. Prefix a field with - for descending order.",
)

STATUS_PARAM = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Filter by status value supported by the resource.",
)

COURSE_PARAM = OpenApiParameter(
    name="course",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by course identifier.",
)

LESSON_PARAM = OpenApiParameter(
    name="lesson",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by lesson identifier.",
)

SECTION_PARAM = OpenApiParameter(
    name="section",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by section identifier.",
)

STUDENT_PARAM = OpenApiParameter(
    name="student",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by student identifier.",
)

START_DATE_PARAM = OpenApiParameter(
    name="start_date",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    description="Inclusive UTC start date filter in YYYY-MM-DD format.",
)

END_DATE_PARAM = OpenApiParameter(
    name="end_date",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    description="Inclusive UTC end date filter in YYYY-MM-DD format.",
)