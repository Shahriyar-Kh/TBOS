from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


def _send_email(subject, message, recipient_email):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[recipient_email],
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return

    try:
        _send_email(
            subject="Welcome to TechBuilt Open School",
            message=(
                f"Hi {user.first_name},\n\n"
                "Welcome to TechBuilt Open School. Your account has been created successfully."
            ),
            recipient_email=user.email,
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, verification_url):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        _send_email(
            subject="Verify your email – TechBuilt Open School",
            message=f"Hi {user.first_name},\n\nPlease verify your email: {verification_url}",
            recipient_email=user.email,
        )
    except User.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, reset_url):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        _send_email(
            subject="Password Reset – TechBuilt Open School",
            message=f"Hi {user.first_name},\n\nReset your password: {reset_url}",
            recipient_email=user.email,
        )
    except User.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
