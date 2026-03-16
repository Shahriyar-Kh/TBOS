import secrets

from django.db import migrations, models
from django.utils import timezone


def populate_verification_codes(apps, schema_editor):
    Certificate = apps.get_model("certificates", "Certificate")
    for certificate in Certificate.objects.filter(verification_code__isnull=True):
        code = secrets.token_urlsafe(24)
        while Certificate.objects.filter(verification_code=code).exists():
            code = secrets.token_urlsafe(24)
        certificate.verification_code = code
        certificate.save(update_fields=["verification_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="certificate",
            old_name="issued_at",
            new_name="issue_date",
        ),
        migrations.RenameField(
            model_name="certificate",
            old_name="pdf_url",
            new_name="certificate_url",
        ),
        migrations.AddField(
            model_name="certificate",
            name="verification_code",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.RunPython(populate_verification_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="certificate",
            name="certificate_number",
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name="certificate",
            name="issue_date",
            field=models.DateField(default=timezone.now),
        ),
        migrations.AlterField(
            model_name="certificate",
            name="verification_code",
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name="certificate",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="certificate",
            constraint=models.UniqueConstraint(
                fields=("student", "course"),
                name="unique_certificate_per_student_course",
            ),
        ),
        migrations.RemoveIndex(
            model_name="certificate",
            name="certificate_student_edaef1_idx",
        ),
        migrations.AddIndex(
            model_name="certificate",
            index=models.Index(fields=["student"], name="cert_student_idx"),
        ),
        migrations.AddIndex(
            model_name="certificate",
            index=models.Index(fields=["course"], name="cert_course_idx"),
        ),
        migrations.AddIndex(
            model_name="certificate",
            index=models.Index(fields=["verification_code"], name="cert_verify_code_idx"),
        ),
    ]
