from rest_framework import serializers

from apps.reviews.models import Review, ReviewResponse


# ──────────────────────────────────────────────
# Student serializers
# ──────────────────────────────────────────────


class ReviewCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review_text = serializers.CharField(max_length=2000)

    def validate(self, attrs):
        from apps.courses.models import Course
        from apps.enrollments.models import Enrollment

        request = self.context["request"]
        course_id = attrs["course_id"]

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course_id": "Course not found."})

        # Instructor cannot review own course
        if course.instructor == request.user:
            raise serializers.ValidationError(
                "You cannot review your own course."
            )

        # Must be enrolled
        if not Enrollment.objects.filter(
            student=request.user, course=course, is_active=True
        ).exists():
            raise serializers.ValidationError(
                "You must be enrolled in this course to review it."
            )

        # One review per course
        if Review.objects.filter(student=request.user, course=course).exists():
            raise serializers.ValidationError(
                "You have already reviewed this course."
            )

        attrs["course"] = course
        return attrs


class ReviewUpdateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    review_text = serializers.CharField(max_length=2000, required=False)


class InstructorResponseReadSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True
    )

    class Meta:
        model = ReviewResponse
        fields = ["id", "instructor_name", "response_text", "created_at"]
        read_only_fields = fields


class ReviewDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )
    instructor_response = InstructorResponseReadSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "rating",
            "review_text",
            "status",
            "instructor_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ReviewListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )
    has_response = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "student_name",
            "course",
            "rating",
            "review_text",
            "status",
            "has_response",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_response(self, obj):
        return hasattr(obj, "instructor_response") and obj.instructor_response is not None


# ──────────────────────────────────────────────
# Instructor serializers
# ──────────────────────────────────────────────


class InstructorResponseSerializer(serializers.Serializer):
    review_id = serializers.UUIDField()
    response_text = serializers.CharField(max_length=2000)


# ──────────────────────────────────────────────
# Admin serializers
# ──────────────────────────────────────────────


class AdminReviewModerateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[Review.Status.PUBLISHED, Review.Status.REJECTED]
    )
