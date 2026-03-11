import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
        ("lessons", "0001_initial"),
    ]

    operations = [
        # 1. Create CourseSection table
        migrations.CreateModel(
            name="CourseSection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True, default="")),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                (
                    "course",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="courses.course",
                    ),
                ),
            ],
            options={
                "db_table": "course_sections",
                "ordering": ["order"],
            },
        ),
        migrations.AddIndex(
            model_name="coursesection",
            index=models.Index(
                fields=["course"], name="course_sections_course_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coursesection",
            index=models.Index(
                fields=["order"], name="course_sections_order_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coursesection",
            index=models.Index(
                fields=["course", "order"], name="course_sections_co_or_idx"
            ),
        ),
        # 2. Remove old unique_together from Lesson
        migrations.AlterUniqueTogether(
            name="lesson",
            unique_together=set(),
        ),
        # 3. Remove old indexes from Lesson
        migrations.RemoveIndex(
            model_name="lesson",
            name="lessons_course__eb1bdb_idx",
        ),
        # 4. Add new fields to Lesson (nullable first to handle existing rows)
        migrations.AddField(
            model_name="lesson",
            name="section",
            field=models.ForeignKey(
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lessons",
                to="lessons.coursesection",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="lesson_type",
            field=models.CharField(
                choices=[
                    ("video", "Video"),
                    ("quiz", "Quiz"),
                    ("assignment", "Assignment"),
                    ("article", "Article"),
                ],
                db_index=True,
                default="video",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="article_content",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RenameField(
            model_name="lesson",
            old_name="duration_minutes",
            new_name="duration_seconds",
        ),
        migrations.RenameField(
            model_name="lesson",
            old_name="is_published",
            new_name="is_preview",
        ),
        # 5. Remove old course FK from Lesson
        migrations.RemoveField(
            model_name="lesson",
            name="course",
        ),
        # 6. Make section non-nullable now
        migrations.AlterField(
            model_name="lesson",
            name="section",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lessons",
                to="lessons.coursesection",
            ),
        ),
        # 7. Add new indexes to Lesson
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(fields=["section"], name="lessons_section_idx"),
        ),
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(fields=["order"], name="lessons_order_idx"),
        ),
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(
                fields=["section", "order"], name="lessons_section_order_idx"
            ),
        ),
    ]
