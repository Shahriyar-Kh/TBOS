import pytest
from datetime import timedelta
from django.utils import timezone

from apps.lessons.models import Lesson
from apps.notifications.models import Notification
from tests.factories import (
    AssignmentFactory,
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    NotificationFactory,
    NotificationPreferenceFactory,
    QuizFactory,
)


@pytest.mark.django_db
class TestNotificationViews:
    def test_list_only_returns_authenticated_user_notifications(self, auth_client, student_user):
        unread_notification = NotificationFactory(recipient=student_user, is_read=False)
        NotificationFactory(recipient=student_user, is_read=True)
        NotificationFactory()

        response = auth_client.get("/api/v1/notifications/")

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["data"]["count"] == 2
        assert response.data["data"]["results"][0]["id"] == str(unread_notification.id)
        assert response.data["data"]["results"][0]["is_read"] is False

    def test_mark_notification_read_rejects_other_users_notification(self, auth_client):
        other_notification = NotificationFactory()

        response = auth_client.put(f"/api/v1/notifications/{other_notification.id}/read/")

        assert response.status_code == 404
        assert response.data["success"] is False

    def test_mark_all_notifications_read(self, auth_client, student_user):
        NotificationFactory.create_batch(3, recipient=student_user, is_read=False)

        response = auth_client.put("/api/v1/notifications/read-all/")

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["data"]["updated_count"] == 3
        assert Notification.objects.filter(recipient=student_user, is_read=False).count() == 0

    def test_get_and_update_preferences(self, auth_client, student_user):
        NotificationPreferenceFactory(
            user=student_user,
            email_notifications_enabled=True,
            quiz_notifications=True,
        )

        get_response = auth_client.get("/api/v1/notifications/preferences/")
        put_response = auth_client.put(
            "/api/v1/notifications/preferences/",
            {
                "email_notifications_enabled": False,
                "in_app_notifications_enabled": True,
                "course_updates": True,
                "assignment_notifications": False,
                "quiz_notifications": False,
            },
            format="json",
        )

        assert get_response.status_code == 200
        assert get_response.data["data"]["email_notifications_enabled"] is True
        assert put_response.status_code == 200
        assert put_response.data["data"]["email_notifications_enabled"] is False
        assert put_response.data["data"]["assignment_notifications"] is False

    def test_admin_broadcast_requires_admin(self, auth_client):
        response = auth_client.post(
            "/api/v1/admin/notifications/broadcast/",
            {"title": "System maintenance", "message": "Scheduled maintenance tonight."},
            format="json",
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestNotificationSignals:
    def test_new_lesson_creates_notifications_for_enrolled_students(self, student_user):
        course = CourseFactory()
        EnrollmentFactory(student=student_user, course=course, is_active=True)
        section = CourseSectionFactory(course=course)

        Lesson.objects.create(
            section=section,
            title="Async Django",
            description="Signals and events",
            lesson_type=Lesson.LessonType.VIDEO,
            order=1,
        )

        notification = Notification.objects.filter(recipient=student_user).first()
        assert notification is not None
        assert notification.notification_type == Notification.NotificationType.NEW_LESSON

    def test_assignment_publish_creates_deadline_notifications(self, student_user):
        course = CourseFactory()
        EnrollmentFactory(student=student_user, course=course, is_active=True)

        AssignmentFactory(
            course=course,
            is_published=True,
            due_date=timezone.now() + timedelta(days=2),
        )

        notification = Notification.objects.filter(recipient=student_user).first()
        assert notification is not None
        assert notification.notification_type == Notification.NotificationType.ASSIGNMENT_DEADLINE

    def test_quiz_activation_creates_notifications(self, student_user):
        course = CourseFactory()
        EnrollmentFactory(student=student_user, course=course, is_active=True)

        QuizFactory(course=course, is_active=True)

        notification = Notification.objects.filter(recipient=student_user).first()
        assert notification is not None
        assert notification.notification_type == Notification.NotificationType.QUIZ_AVAILABLE