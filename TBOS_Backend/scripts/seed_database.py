"""
Seed the database with initial data for development.

Usage:
    python manage.py shell < scripts/seed_database.py
    OR
    python manage.py runscript seed_database  (with django-extensions)
"""

import json
import os
import sys

import django

# Ensure the project is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.courses.models import Category, Level, Language  # noqa: E402


def seed():
    categories = [
        {"name": "Web Development", "icon": "code"},
        {"name": "Data Science", "icon": "bar_chart"},
        {"name": "Mobile Development", "icon": "phone_android"},
        {"name": "DevOps", "icon": "cloud"},
        {"name": "Machine Learning", "icon": "psychology"},
        {"name": "Programming Languages", "icon": "terminal"},
    ]
    for cat in categories:
        Category.objects.get_or_create(name=cat["name"], defaults=cat)

    levels = ["Beginner", "Intermediate", "Advanced", "All Levels"]
    for name in levels:
        Level.objects.get_or_create(name=name)

    languages = ["English", "Hindi", "Urdu", "Spanish", "French"]
    for name in languages:
        Language.objects.get_or_create(name=name)

    # Load data.json if it exists
    data_file = os.path.join(os.path.dirname(__file__), "data.json")
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Loaded {len(data)} records from data.json")

    print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
