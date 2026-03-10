"""
Import courses from a JSON file into the database.

Usage:
    python scripts/import_courses.py --file scripts/data.json

The JSON should be a list of objects with keys matching the Course model fields.
"""

import argparse
import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from apps.courses.models import Course, Category  # noqa: E402

User = get_user_model()


def import_courses(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print("JSON file must contain a list of course records.")
        return

    created = 0
    for record in records:
        title = record.get("title")
        if not title:
            continue
        if Course.objects.filter(title=title).exists():
            print(f"  Skipping (exists): {title}")
            continue

        # Resolve instructor
        instructor_email = record.get("instructor_email")
        instructor = User.objects.filter(email=instructor_email).first() if instructor_email else None
        if not instructor:
            instructor = User.objects.filter(role="admin").first()

        # Resolve category
        category_name = record.get("category")
        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)

        Course.objects.create(
            title=title,
            description=record.get("description", ""),
            instructor=instructor,
            category=category,
            price=record.get("price", 0),
            is_free=record.get("is_free", True),
            status=record.get("status", "draft"),
        )
        created += 1
        print(f"  Created: {title}")

    print(f"\nImported {created} courses.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import courses from JSON")
    parser.add_argument("--file", default="scripts/data.json", help="Path to JSON file")
    args = parser.parse_args()
    import_courses(args.file)
