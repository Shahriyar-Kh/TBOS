from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, verification_url):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Verify your email – TechBuilt Open School",
            message=f"Hi {user.first_name},\n\nPlease verify your email: {verification_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
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
        send_mail(
            subject="Password Reset – TechBuilt Open School",
            message=f"Hi {user.first_name},\n\nReset your password: {reset_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except User.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
