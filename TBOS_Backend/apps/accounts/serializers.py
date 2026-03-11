from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Profile
from apps.core.validators import validate_file_size

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[User.Role.STUDENT, User.Role.INSTRUCTOR],
        default=User.Role.STUDENT,
        required=False,
    )

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower().strip()

    def validate_username(self, value):
        if value and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value.strip()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "avatar",
            "bio",
            "headline",
            "country",
            "city",
            "timezone",
            "phone_number",
            "website",
            "linkedin",
            "github",
            "twitter",
            "skills",
            "education",
            "experience",
            "profile_visibility",
            "date_created",
            "date_updated",
        ]
        read_only_fields = ["id", "date_created", "date_updated"]

    def validate_avatar(self, value):
        if value:
            validate_file_size(value)
        return value


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "google_account",
            "is_active",
            "date_joined",
            "last_login",
            "profile",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_verified",
            "google_account",
            "is_active",
            "date_joined",
            "last_login",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "avatar",
            "bio",
            "headline",
            "country",
            "city",
            "timezone",
            "phone_number",
            "website",
            "linkedin",
            "github",
            "twitter",
            "skills",
            "education",
            "experience",
            "profile_visibility",
        ]

    def validate_avatar(self, value):
        if value:
            validate_file_size(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_verified",
            "google_account",
            "date_joined",
            "last_login",
            "profile",
        ]
        read_only_fields = ["id", "email", "date_joined"]
