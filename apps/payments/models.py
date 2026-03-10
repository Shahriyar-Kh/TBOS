from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        MANUAL = "manual", "Manual"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.STRIPE,
    )
    provider_payment_id = models.CharField(
        max_length=200, blank=True, default="", db_index=True
    )
    provider_checkout_id = models.CharField(
        max_length=200, blank=True, default=""
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    receipt_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.course.title if self.course else 'N/A'} — {self.status}"


class BillingDetails(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_details",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        db_table = "billing_details"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
