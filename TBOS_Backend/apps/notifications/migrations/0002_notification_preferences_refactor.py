import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_notification_types(apps, schema_editor):
    Notification = apps.get_model("notifications", "Notification")
    mapping = {
        "assignment": "ASSIGNMENT_DEADLINE",
        "quiz": "QUIZ_AVAILABLE",
        "certificate": "CERTIFICATE_ISSUED",
        "announcement": "SYSTEM_ALERT",
        "enrollment": "SYSTEM_ALERT",
        "payment": "SYSTEM_ALERT",
        "grade": "SYSTEM_ALERT",
        "system": "SYSTEM_ALERT",
    }
    for old_value, new_value in mapping.items():
        Notification.objects.filter(notification_type=old_value).update(notification_type=new_value)


def create_preferences_for_existing_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    NotificationPreference = apps.get_model("notifications", "NotificationPreference")
    preferences = []
    existing_user_ids = set(
        NotificationPreference.objects.values_list("user_id", flat=True)
    )
    for user_id in User.objects.exclude(id__in=existing_user_ids).values_list("id", flat=True):
        preferences.append(
            NotificationPreference(
                id=uuid.uuid4(),
                user_id=user_id,
                email_notifications_enabled=True,
                in_app_notifications_enabled=True,
                course_updates=True,
                assignment_notifications=True,
                quiz_notifications=True,
            )
        )
    if preferences:
        NotificationPreference.objects.bulk_create(preferences, batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email_notifications_enabled", models.BooleanField(default=True)),
                ("in_app_notifications_enabled", models.BooleanField(default=True)),
                ("course_updates", models.BooleanField(default=True)),
                ("assignment_notifications", models.BooleanField(default=True)),
                ("quiz_notifications", models.BooleanField(default=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "notification_preferences",
            },
        ),
        migrations.AddField(
            model_name="notification",
            name="reference_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("COURSE_UPDATE", "Course Update"),
                    ("NEW_LESSON", "New Lesson"),
                    ("QUIZ_AVAILABLE", "Quiz Available"),
                    ("ASSIGNMENT_DEADLINE", "Assignment Deadline"),
                    ("CERTIFICATE_ISSUED", "Certificate Issued"),
                    ("SYSTEM_ALERT", "System Alert"),
                ],
                db_index=True,
                default="SYSTEM_ALERT",
                max_length=32,
            ),
        ),
        migrations.RemoveField(
            model_name="notification",
            name="action_url",
        ),
        migrations.RemoveIndex(
            model_name="notification",
            name="notificatio_recipie_b1a229_idx",
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "created_at"], name="notificatio_recipie_f22c62_idx"),
        ),
        migrations.RunPython(migrate_notification_types, migrations.RunPython.noop),
        migrations.RunPython(create_preferences_for_existing_users, migrations.RunPython.noop),
    ]