"""
Quiz module enhancement migration.

- Rename fields to match requirements
- Add new fields (shuffle_questions, shuffle_options, question_type, explanation, etc.)
- Rename QuizAnswer to StudentAnswer
- Replace is_completed bool with status choices on QuizAttempt
- Add attempt_number, total_questions, correct_answers to QuizAttempt
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        # ── Quiz model ──────────────────────────────────
        migrations.RenameField(
            model_name="quiz",
            old_name="pass_percentage",
            new_name="passing_score",
        ),
        migrations.RenameField(
            model_name="quiz",
            old_name="is_published",
            new_name="is_active",
        ),
        migrations.AddField(
            model_name="quiz",
            name="shuffle_questions",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="quiz",
            name="shuffle_options",
            field=models.BooleanField(default=False),
        ),
        # Change lesson from ForeignKey to OneToOneField
        migrations.AlterField(
            model_name="quiz",
            name="lesson",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quiz",
                to="lessons.lesson",
            ),
        ),

        # ── Question model ──────────────────────────────
        migrations.RenameField(
            model_name="question",
            old_name="text",
            new_name="question_text",
        ),
        migrations.AddField(
            model_name="question",
            name="question_type",
            field=models.CharField(
                choices=[("mcq", "Multiple Choice")],
                default="mcq",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="explanation",
            field=models.TextField(blank=True, default=""),
        ),

        # ── Option model ────────────────────────────────
        migrations.RenameField(
            model_name="option",
            old_name="text",
            new_name="option_text",
        ),

        # ── QuizAttempt model ────────────────────────────
        # Remove old index that references is_completed
        migrations.RemoveIndex(
            model_name="quizattempt",
            name="quiz_attemp_student_6f7b9b_idx",
        ),
        # Rename time fields
        migrations.RenameField(
            model_name="quizattempt",
            old_name="started_at",
            new_name="start_time",
        ),
        migrations.RenameField(
            model_name="quizattempt",
            old_name="completed_at",
            new_name="end_time",
        ),
        # Add new fields
        migrations.AddField(
            model_name="quizattempt",
            name="attempt_number",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="total_questions",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="correct_answers",
            field=models.PositiveIntegerField(default=0),
        ),
        # Add status field
        migrations.AddField(
            model_name="quizattempt",
            name="status",
            field=models.CharField(
                choices=[
                    ("in_progress", "In Progress"),
                    ("submitted", "Submitted"),
                    ("expired", "Expired"),
                ],
                default="in_progress",
                max_length=20,
            ),
        ),
        # Remove old fields
        migrations.RemoveField(
            model_name="quizattempt",
            name="is_completed",
        ),
        migrations.RemoveField(
            model_name="quizattempt",
            name="current_question_index",
        ),
        # Add new index
        migrations.AddIndex(
            model_name="quizattempt",
            index=models.Index(
                fields=["student", "status"],
                name="quiz_attemp_student_status_idx",
            ),
        ),

        # ── Rename QuizAnswer to StudentAnswer ──────────
        migrations.RenameModel(
            old_name="QuizAnswer",
            new_name="StudentAnswer",
        ),
        migrations.AlterModelTable(
            name="studentanswer",
            table="student_answers",
        ),
        # Update related_name on question FK
        migrations.AlterField(
            model_name="studentanswer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="student_answers",
                to="quiz.question",
            ),
        ),
    ]
