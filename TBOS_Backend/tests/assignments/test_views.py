"""Tests for assignment API views."""
import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission
from apps.courses.models import Course
from apps.lessons.models import Lesson
from tests.factories import (
    AdminFactory,
    AssignmentFactory,
    AssignmentSubmissionFactory,
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    UserFactory,
)

BASE = "/api/v1/assignments"


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
def assignment_lesson(course):
    section = CourseSectionFactory(course=course)
    return LessonFactory(section=section, lesson_type=Lesson.LessonType.ASSIGNMENT)


@pytest.fixture
def assignment(course, assignment_lesson):
    return AssignmentFactory(
        course=course,
        lesson=assignment_lesson,
        is_published=True,
        max_attempts=3,
        allow_resubmission=True,
    )


@pytest.fixture
def enrolled_student(student, course):
    EnrollmentFactory(student=student, course=course)
    return student


# ──────────────────────────────────────────────
# Instructor: Assignment CRUD
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorAssignmentCRUD:
    url = f"{BASE}/instructor/"

    def test_create_assignment(self, api_client, instructor, course, assignment_lesson):
        client = auth(api_client, instructor)
        data = {
            "course": str(course.id),
            "lesson": str(assignment_lesson.id),
            "title": "Build a REST API",
            "description": "Create a Django REST API project.",
            "instructions": "Use best practices.",
            "max_score": 100,
            "submission_type": "file_and_text",
            "max_attempts": 3,
            "allow_resubmission": True,
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["success"] is True
        assert resp.data["data"]["title"] == "Build a REST API"

    def test_list_assignments(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_retrieve_assignment(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        resp = client.get(f"{self.url}{assignment.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["id"] == str(assignment.id)

    def test_update_assignment(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        data = {
            "course": str(assignment.course_id),
            "title": "Updated Title",
            "description": assignment.description,
            "max_score": 50,
            "submission_type": "text",
            "max_attempts": 1,
        }
        resp = client.put(f"{self.url}{assignment.id}/", data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["title"] == "Updated Title"

    def test_partial_update_assignment(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        resp = client.patch(f"{self.url}{assignment.id}/", {"title": "Patched"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["title"] == "Patched"

    def test_delete_assignment(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        resp = client.delete(f"{self.url}{assignment.id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_student_cannot_create_assignment(self, api_client, student, course, assignment_lesson):
        client = auth(api_client, student)
        data = {
            "course": str(course.id),
            "lesson": str(assignment_lesson.id),
            "title": "Hack",
            "description": "Nope",
            "max_score": 100,
            "submission_type": "text",
            "max_attempts": 1,
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_other_instructor_cannot_see_assignments(self, api_client, assignment):
        other = InstructorFactory()
        client = auth(api_client, other)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        ids = [item["id"] for item in resp.data.get("results", resp.data)]
        assert str(assignment.id) not in ids


# ──────────────────────────────────────────────
# Instructor: View Submissions
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorSubmissions:

    def test_view_submissions(self, api_client, instructor, assignment, enrolled_student):
        AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        client = auth(api_client, instructor)
        resp = client.get(f"{BASE}/instructor/{assignment.id}/submissions/")
        assert resp.status_code == status.HTTP_200_OK


# ──────────────────────────────────────────────
# Instructor: Grade
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorGrading:

    def test_grade_submission(self, api_client, instructor, assignment, enrolled_student):
        sub = AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        client = auth(api_client, instructor)
        data = {
            "submission_id": str(sub.id),
            "score": 85,
            "feedback": "Well done!",
        }
        resp = client.post(f"{BASE}/instructor/grade/", data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True
        sub.refresh_from_db()
        assert sub.status == AssignmentSubmission.Status.GRADED

    def test_grade_exceeds_max_score(self, api_client, instructor, assignment, enrolled_student):
        sub = AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        client = auth(api_client, instructor)
        data = {
            "submission_id": str(sub.id),
            "score": 999,
            "feedback": "",
        }
        resp = client.post(f"{BASE}/instructor/grade/", data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_grade_nonexistent_submission(self, api_client, instructor):
        client = auth(api_client, instructor)
        data = {
            "submission_id": "00000000-0000-0000-0000-000000000000",
            "score": 50,
        }
        resp = client.post(f"{BASE}/instructor/grade/", data, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_other_instructor_cannot_grade(self, api_client, assignment, enrolled_student):
        sub = AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        other = InstructorFactory()
        client = auth(api_client, other)
        data = {"submission_id": str(sub.id), "score": 50}
        resp = client.post(f"{BASE}/instructor/grade/", data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Student: Submit Assignment
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentSubmit:

    def test_submit_assignment(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        data = {
            "submission_text": "Here is my solution.",
            "file_url": "https://s3.example.com/file.pdf",
        }
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["success"] is True
        assert resp.data["data"]["attempt_number"] == 1

    def test_submit_multiple_attempts(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        data = {"submission_text": "Attempt 1", "file_url": "https://s3.example.com/f.pdf"}
        resp1 = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        data["submission_text"] = "Attempt 2"
        resp2 = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp2.status_code == status.HTTP_201_CREATED
        assert resp2.data["data"]["attempt_number"] == 2

    def test_submit_exceeds_max_attempts(self, api_client, enrolled_student, assignment):
        assignment.max_attempts = 1
        assignment.save()
        client = auth(api_client, enrolled_student)
        data = {"submission_text": "Only one", "file_url": "https://s3.example.com/f.pdf"}
        resp1 = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED
        resp2 = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_not_enrolled(self, api_client, student, assignment):
        client = auth(api_client, student)
        data = {"submission_text": "Hello"}
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        # Student can't even see unpublished assignments they're not enrolled in
        assert resp.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST)

    def test_submit_text_only_assignment_requires_text(self, api_client, enrolled_student, assignment):
        assignment.submission_type = Assignment.SubmissionType.TEXT
        assignment.save()
        client = auth(api_client, enrolled_student)
        data = {"file_url": "https://s3.example.com/f.pdf"}
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_file_only_assignment_requires_file(self, api_client, enrolled_student, assignment):
        assignment.submission_type = Assignment.SubmissionType.FILE
        assignment.save()
        client = auth(api_client, enrolled_student)
        data = {"submission_text": "Just text"}
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_rejects_disallowed_file_extension(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        data = {
            "submission_text": "Answer",
            "file_url": "https://s3.example.com/hack.exe",
        }
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_instructor_cannot_submit(self, api_client, instructor, assignment):
        client = auth(api_client, instructor)
        data = {"submission_text": "Instructors shouldn't submit"}
        resp = client.post(f"{BASE}/student/{assignment.id}/submit/", data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Student: View Submissions & Results
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentViewSubmissions:

    def test_my_submissions(self, api_client, enrolled_student, assignment):
        AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=2,
        )
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/my-submissions/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]) == 2

    def test_result(self, api_client, enrolled_student, assignment):
        sub = AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student,
            attempt_number=1, status=AssignmentSubmission.Status.GRADED,
        )
        from tests.factories import AssignmentGradeFactory
        AssignmentGradeFactory(submission=sub, score=90, feedback="Excellent")

        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/result/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["grade"]["score"] == 90

    def test_result_no_graded_submission(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/result/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_see_other_student_submissions(self, api_client, assignment, enrolled_student):
        other_student = UserFactory()
        EnrollmentFactory(student=other_student, course=assignment.course)
        AssignmentSubmissionFactory(
            assignment=assignment, student=other_student, attempt_number=1,
        )
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/my-submissions/")
        assert resp.status_code == status.HTTP_200_OK
        # Enrolled student has no submissions
        assert len(resp.data["data"]) == 0


# ──────────────────────────────────────────────
# Student: List & Retrieve Assignments
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentAssignmentList:

    def test_list_enrolled_assignments(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/")
        assert resp.status_code == status.HTTP_200_OK

    def test_retrieve_assignment_detail(self, api_client, enrolled_student, assignment):
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(assignment.id)

    def test_unpublished_assignment_not_visible(self, api_client, enrolled_student, assignment):
        assignment.is_published = False
        assignment.save()
        client = auth(api_client, enrolled_student)
        resp = client.get(f"{BASE}/student/{assignment.id}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ──────────────────────────────────────────────
# Admin tests
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAdminAccess:

    def test_admin_can_list_all_assignments(self, api_client, admin, assignment):
        client = auth(api_client, admin)
        resp = client.get(f"{BASE}/instructor/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_can_grade(self, api_client, admin, assignment, enrolled_student):
        sub = AssignmentSubmissionFactory(
            assignment=assignment, student=enrolled_student, attempt_number=1,
        )
        client = auth(api_client, admin)
        data = {"submission_id": str(sub.id), "score": 95, "feedback": "Admin graded"}
        resp = client.post(f"{BASE}/instructor/grade/", data, format="json")
        assert resp.status_code == status.HTTP_200_OK
