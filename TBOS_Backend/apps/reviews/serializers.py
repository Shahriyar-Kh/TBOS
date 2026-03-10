from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "rating",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "student", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["course", "rating", "content"]

    def validate(self, attrs):
        request = self.context["request"]
        course = attrs["course"]
        # Must be enrolled
        if not course.enrollments.filter(
            student=request.user, is_active=True
        ).exists():
            raise serializers.ValidationError(
                "You must be enrolled in this course to review it."
            )
        # One review per course
        if Review.objects.filter(student=request.user, course=course).exists():
            raise serializers.ValidationError(
                "You have already reviewed this course."
            )
        return attrs
