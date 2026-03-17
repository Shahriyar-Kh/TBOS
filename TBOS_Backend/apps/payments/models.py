from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Order(TimeStampedModel):
    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    class PaymentMethod(models.TextChoices):
        STRIPE = "STRIPE", "Stripe"
        EASYPAISA = "EASYPAISA", "EasyPaisa"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="orders",
        db_index=True,
    )
    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.STRIPE,
    )

    class Meta:
        db_table = "orders"
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_order"),
        ]
        indexes = [
            models.Index(fields=["student"], name="orders_stude_8ff1e4_idx"),
            models.Index(fields=["course"], name="orders_cours_d913ec_idx"),
            models.Index(fields=["order_status"], name="orders_order_8b56dc_idx"),
            models.Index(fields=["student", "order_status"], name="orders_stude_336cf7_idx"),
        ]

    def __str__(self):
        return f"{self.order_number} | {self.student.email} | {self.course.title}"


class Payment(TimeStampedModel):
    class Provider(models.TextChoices):
        STRIPE = "STRIPE", "Stripe"
        EASYPAISA = "EASYPAISA", "EasyPaisa"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payment_provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.STRIPE,
    )
    transaction_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    payment_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["payment_status"], name="payments_paym_9f1a56_idx"),
            models.Index(fields=["payment_provider", "payment_status"], name="payments_paym_093805_idx"),
        ]

    def __str__(self):
        return f"{self.order.order_number} | {self.payment_provider} | {self.payment_status}"


class BillingDetails(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_details",
        db_index=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        db_table = "billing_details"
        indexes = [
            models.Index(fields=["user", "created_at"], name="billing_det_user_id_987320_idx"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
