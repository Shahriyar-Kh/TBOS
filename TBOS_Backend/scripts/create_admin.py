"""
Create a superuser (admin) non-interactively.

Usage:
    python scripts/create_admin.py

Environment variables:
    ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FIRST_NAME, ADMIN_LAST_NAME
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()


def create_admin():
    email = os.environ.get("ADMIN_EMAIL", "admin@tbos.dev")
    password = os.environ.get("ADMIN_PASSWORD", "admin123456")
    first_name = os.environ.get("ADMIN_FIRST_NAME", "Admin")
    last_name = os.environ.get("ADMIN_LAST_NAME", "User")

    if User.objects.filter(email=email).exists():
        print(f"Admin user {email} already exists.")
        return

    User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    print(f"Admin user created: {email}")


if __name__ == "__main__":
    create_admin()
