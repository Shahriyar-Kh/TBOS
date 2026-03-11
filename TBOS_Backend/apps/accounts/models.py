import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils import timezone as django_timezone

from apps.accounts.managers import CustomUserManager
from apps.core.validators import validate_file_size


class User(AbstractBaseUser, PermissionsMixin):
    """Production-grade custom user model for TBOS accounts."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        INSTRUCTOR = "instructor", "Instructor"
        STUDENT = "student", "Student"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    google_account = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=django_timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)


class Profile(models.Model):
    """Professional LMS profile for students and instructors."""

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_file_size,
        ],
    )
    bio = models.TextField(max_length=1000, blank=True, default="")
    headline = models.CharField(max_length=200, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    timezone = models.CharField(max_length=100, blank=True, default="UTC")
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[0-9+()\-\s]{7,20}$", "Enter a valid phone number.")],
    )
    website = models.URLField(max_length=300, blank=True, default="")
    linkedin = models.URLField(max_length=300, blank=True, default="")
    github = models.URLField(max_length=300, blank=True, default="")
    twitter = models.URLField(max_length=300, blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    education = models.TextField(blank=True, default="")
    experience = models.TextField(blank=True, default="")
    profile_visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    date_created = models.DateTimeField(default=django_timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"
        indexes = [models.Index(fields=["profile_visibility"])]

    def __str__(self):
        return f"Profile: {self.user.email}"
