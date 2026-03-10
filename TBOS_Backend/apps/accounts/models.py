import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import CustomUserManager


class User(AbstractUser):
    """Custom user model with email login and role-based access."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        INSTRUCTOR = "instructor", "Instructor"
        STUDENT = "student", "Student"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # remove username field
    email = models.EmailField("email address", unique=True, db_index=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email", "role"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Profile(models.Model):
    """Extended user profile."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.URLField(max_length=500, blank=True, default="")
    bio = models.TextField(max_length=1000, blank=True, default="")
    headline = models.CharField(max_length=200, blank=True, default="")
    website = models.URLField(max_length=300, blank=True, default="")
    linkedin = models.URLField(max_length=300, blank=True, default="")
    twitter = models.URLField(max_length=300, blank=True, default="")
    github = models.URLField(max_length=300, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return f"Profile: {self.user.email}"
