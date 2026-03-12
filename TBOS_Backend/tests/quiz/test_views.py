"""Tests for quiz API views."""
import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course
from apps.lessons.models import Lesson
from apps.quiz.models import Quiz, QuizAttempt
from tests.factories import (
    AdminFactory,
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    OptionFactory,
    QuestionFactory,
    QuizAttemptFactory,
    QuizFactory,
    UserFactory,
)

BASE = "/api/v1/quiz"


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def admin(db):
    return AdminFactory()


def auth(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def course(instructor):
    return CourseFactory(instructor=instructor, status=Course.Status.PUBLISHED)


@pytest.fixture
def quiz_lesson(course):
    section = CourseSectionFactory(course=course)
    return LessonFactory(section=section, lesson_type=Lesson.LessonType.QUIZ)


@pytest.fixture
def quiz(course, quiz_lesson):
    return QuizFactory(course=course, lesson=quiz_lesson, is_active=True)


@pytest.fixture
def quiz_with_questions(quiz):
    questions = []
    for i in range(3):
        q = QuestionFactory(quiz=quiz, question_text=f"Question {i+1}", order=i, points=1)
        OptionFactory(question=q, option_text="Wrong A", is_correct=False, order=0)
        OptionFactory(question=q, option_text="Wrong B", is_correct=False, order=1)
        OptionFactory(question=q, option_text="Correct", is_correct=True, order=2)
        questions.append(q)
    return quiz, questions


@pytest.fixture
def enrolled_student(student, course):
    EnrollmentFactory(student=student, course=course)
    return student


# ──────────────────────────────────────────────
# Instructor: Quiz CRUD
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorQuizCRUD:
    url = f"{BASE}/instructor/quizzes/"

    def test_create_quiz(self, api_client, instructor, course, quiz_lesson):
        client = auth(api_client, instructor)
        data = {
            "course": str(course.id),
            "lesson": str(quiz_lesson.id),
            "title": "New Quiz",
            "description": "Test description",
            "time_limit_minutes": 30,
            "max_attempts": 3,
            "passing_score": 60,
        }
        response = client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["title"] == "New Quiz"

    def test_list_quizzes(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_retrieve_quiz(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        response = client.get(f"{self.url}{quiz.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["id"] == str(quiz.id)

    def test_update_quiz(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        response = client.patch(
            f"{self.url}{quiz.id}/",
            {"title": "Updated Quiz"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Quiz"

    def test_delete_quiz(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        response = client.delete(f"{self.url}{quiz.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert not Quiz.objects.filter(id=quiz.id).exists()

    def test_student_cannot_access_instructor_api(self, api_client, student, quiz):
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# Instructor: Question CRUD
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorQuestionCRUD:
    url = f"{BASE}/instructor/questions/"

    def test_create_question(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        data = {
            "quiz": str(quiz.id),
            "question_text": "What is REST?",
            "points": 2,
            "order": 0,
        }
        response = client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_list_questions_by_quiz(self, api_client, instructor, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, instructor)
        response = client.get(f"{self.url}?quiz={quiz.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3

    def test_delete_question(self, api_client, instructor, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, instructor)
        response = client.delete(f"{self.url}{questions[0].id}/")
        assert response.status_code == status.HTTP_200_OK


# ──────────────────────────────────────────────
# Instructor: Option CRUD
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorOptionCRUD:
    url = f"{BASE}/instructor/options/"

    def test_create_option(self, api_client, instructor, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, instructor)
        data = {
            "question": str(questions[0].id),
            "option_text": "New Option",
            "is_correct": False,
            "order": 10,
        }
        response = client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_list_options_by_question(self, api_client, instructor, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, instructor)
        response = client.get(f"{self.url}?question={questions[0].id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3  # 3 options per question


# ──────────────────────────────────────────────
# Admin: Quiz management
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAdminQuizManagement:
    url = f"{BASE}/admin/quizzes/"

    def test_admin_list_all_quizzes(self, api_client, admin, quiz):
        client = auth(api_client, admin)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_admin_delete_quiz(self, api_client, admin, quiz):
        client = auth(api_client, admin)
        response = client.delete(f"{self.url}{quiz.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_student_cannot_access_admin_api(self, api_client, student):
        client = auth(api_client, student)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Student: Quiz attempt workflow
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentQuizWorkflow:
    base_url = f"{BASE}/student/"

    def test_list_quizzes(self, api_client, enrolled_student, quiz):
        client = auth(api_client, enrolled_student)
        response = client.get(self.base_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_start_quiz(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        response = client.post(f"{self.base_url}{quiz.id}/start/")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "attempt" in response.data["data"]
        assert "questions" in response.data["data"]

    def test_start_resume_existing(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")
        response = client.post(f"{self.base_url}{quiz.id}/start/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_questions(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        response = client.get(f"{self.base_url}{quiz.id}/questions/")
        assert response.status_code == status.HTTP_200_OK
        # Verify correct answers are hidden
        for q in response.data["data"]:
            for opt in q["options"]:
                assert "is_correct" not in opt

    def test_submit_answer(self, api_client, enrolled_student, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")

        correct_option = questions[0].options.get(is_correct=True)
        response = client.post(
            f"{self.base_url}{quiz.id}/submit-answer/",
            {"question_id": str(questions[0].id), "option_id": str(correct_option.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["submitted"] is True

    def test_submit_quiz(self, api_client, enrolled_student, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")

        # Answer all questions correctly
        for q in questions:
            correct = q.options.get(is_correct=True)
            client.post(
                f"{self.base_url}{quiz.id}/submit-answer/",
                {"question_id": str(q.id), "option_id": str(correct.id)},
                format="json",
            )

        response = client.post(f"{self.base_url}{quiz.id}/submit/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["score"] == 3
        assert data["correct_answers"] == 3
        assert data["status"] == "submitted"
        assert data["passed"] is True

    def test_get_results(self, api_client, enrolled_student, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")
        client.post(f"{self.base_url}{quiz.id}/submit/")

        response = client.get(f"{self.base_url}{quiz.id}/result/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) == 1

    def test_no_result_before_submission(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")

        response = client.get(f"{self.base_url}{quiz.id}/result/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_max_attempts_enforced(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        quiz.max_attempts = 1
        quiz.save()

        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")
        client.post(f"{self.base_url}{quiz.id}/submit/")

        response = client.post(f"{self.base_url}{quiz.id}/start/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unenrolled_cannot_start(self, api_client, quiz_with_questions):
        quiz, _ = quiz_with_questions
        unenrolled = UserFactory()
        client = auth(api_client, unenrolled)
        response = client.post(f"{self.base_url}{quiz.id}/start/")
        # Student role but not enrolled — quiz not in queryset, so 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_instructor_cannot_access_student_api(self, api_client, instructor, quiz):
        client = auth(api_client, instructor)
        response = client.get(self.base_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_answer_no_active_attempt(self, api_client, enrolled_student, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, enrolled_student)
        correct = questions[0].options.get(is_correct=True)
        response = client.post(
            f"{self.base_url}{quiz.id}/submit-answer/",
            {"question_id": str(questions[0].id), "option_id": str(correct.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_no_active_attempt(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        response = client.post(f"{self.base_url}{quiz.id}/submit/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────
# Security tests
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestQuizSecurity:
    base_url = f"{BASE}/student/"

    def test_correct_answers_hidden_in_questions(self, api_client, enrolled_student, quiz_with_questions):
        quiz, _ = quiz_with_questions
        client = auth(api_client, enrolled_student)
        response = client.get(f"{self.base_url}{quiz.id}/questions/")
        for q in response.data["data"]:
            for opt in q["options"]:
                assert "is_correct" not in opt

    def test_cannot_modify_after_submission(self, api_client, enrolled_student, quiz_with_questions):
        quiz, questions = quiz_with_questions
        client = auth(api_client, enrolled_student)
        client.post(f"{self.base_url}{quiz.id}/start/")
        client.post(f"{self.base_url}{quiz.id}/submit/")

        correct = questions[0].options.get(is_correct=True)
        response = client.post(
            f"{self.base_url}{quiz.id}/submit-answer/",
            {"question_id": str(questions[0].id), "option_id": str(correct.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
