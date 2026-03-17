import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import Profile, User
from apps.courses.models import Category, Course, Language, LearningOutcome, Level, Requirement
from apps.lessons.models import CourseSection, Lesson
from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
from apps.videos.models import Video, YouTubePlaylistImport
from apps.quiz.models import Quiz, Question, Option, QuizAttempt, StudentAnswer
from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission
from apps.reviews.models import Review, ReviewResponse
from apps.certificates.models import Certificate
from apps.notifications.models import Notification, NotificationPreference
from apps.payments.models import BillingDetails, Order, Payment


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = User.Role.STUDENT
    is_active = True
    is_verified = False
    google_account = False
    password = factory.PostGenerationMethodCall("set_password", "StrongPass123!")

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create:
            instance.save()


class StudentFactory(UserFactory):
    role = User.Role.STUDENT
    email = factory.Sequence(lambda n: f"student{n}@example.com")
    username = factory.Sequence(lambda n: f"student{n}")


class InstructorFactory(UserFactory):
    role = User.Role.INSTRUCTOR
    email = factory.Sequence(lambda n: f"instructor{n}@example.com")
    username = factory.Sequence(lambda n: f"instructor{n}")


class AdminFactory(UserFactory):
    role = User.Role.ADMIN
    is_staff = True
    is_superuser = True
    is_verified = True
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    username = factory.Sequence(lambda n: f"admin{n}")


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    bio = factory.Faker("paragraph", nb_sentences=3)
    headline = factory.Faker("job")
    country = factory.Faker("country")
    city = factory.Faker("city")
    timezone = "UTC"
    phone_number = "+12345678901"
    website = factory.Faker("url")
    linkedin = factory.Faker("url")
    github = factory.Faker("url")
    twitter = factory.Faker("url")
    skills = factory.LazyFunction(lambda: ["Django", "REST", "PostgreSQL"])
    education = factory.Faker("sentence")
    experience = factory.Faker("paragraph", nb_sentences=2)
    profile_visibility = Profile.Visibility.PUBLIC

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = kwargs["user"]
        profile, _ = model_class.objects.get_or_create(user=user)
        for key, value in kwargs.items():
            if key != "user":
                setattr(profile, key, value)
        profile.save()
        return profile


# ──────────────────────────────────────────────
# Course factories
# ──────────────────────────────────────────────


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    icon = "fa-book"


class LevelFactory(DjangoModelFactory):
    class Meta:
        model = Level

    name = factory.Sequence(lambda n: f"Level {n}")


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = Language

    name = factory.Sequence(lambda n: f"Language {n}")


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    instructor = factory.SubFactory(InstructorFactory)
    category = factory.SubFactory(CategoryFactory)
    level = factory.SubFactory(LevelFactory)
    language = factory.SubFactory(LanguageFactory)
    title = factory.Sequence(lambda n: f"Test Course {n}")
    subtitle = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("paragraph", nb_sentences=3)
    price = factory.LazyFunction(lambda: 49.99)
    discount = factory.LazyFunction(lambda: 0.00)
    status = Course.Status.DRAFT
    is_free = False


class LearningOutcomeFactory(DjangoModelFactory):
    class Meta:
        model = LearningOutcome

    course = factory.SubFactory(CourseFactory)
    text = factory.Faker("sentence", nb_words=8)
    order = factory.Sequence(lambda n: n)


class RequirementFactory(DjangoModelFactory):
    class Meta:
        model = Requirement

    course = factory.SubFactory(CourseFactory)
    text = factory.Faker("sentence", nb_words=6)
    order = factory.Sequence(lambda n: n)


# ──────────────────────────────────────────────
# Lesson / curriculum factories
# ──────────────────────────────────────────────


class CourseSectionFactory(DjangoModelFactory):
    class Meta:
        model = CourseSection

    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Section {n}")
    description = factory.Faker("sentence", nb_words=8)
    order = factory.Sequence(lambda n: n)


class SectionFactory(CourseSectionFactory):
    pass


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    section = factory.SubFactory(CourseSectionFactory)
    title = factory.Sequence(lambda n: f"Lesson {n}")
    description = factory.Faker("sentence", nb_words=8)
    lesson_type = Lesson.LessonType.VIDEO
    order = factory.Sequence(lambda n: n)
    is_preview = False
    duration_seconds = 300
    article_content = ""

# ──────────────────────────────────────────────
# Video factories
# ──────────────────────────────────────────────


class VideoFactory(DjangoModelFactory):
    class Meta:
        model = Video

    lesson = factory.SubFactory(LessonFactory)
    course = factory.LazyAttribute(lambda obj: obj.lesson.section.course)
    title = factory.Sequence(lambda n: f"Video {n}")
    description = factory.Faker("sentence", nb_words=6)
    order = factory.Sequence(lambda n: n)
    source_type = Video.SourceType.YOUTUBE
    youtube_id = factory.Sequence(lambda n: f"ytid{n:07d}")
    thumbnail = factory.LazyAttribute(
        lambda obj: f"https://img.youtube.com/vi/{obj.youtube_id}/hqdefault.jpg"
    )
    duration_seconds = 300
    is_preview = False
    is_published = True


class YouTubePlaylistImportFactory(DjangoModelFactory):
    class Meta:
        model = YouTubePlaylistImport

    course = factory.SubFactory(CourseFactory)
    lesson = factory.SubFactory(LessonFactory)
    playlist_url = "https://www.youtube.com/playlist?list=PLtest123"
    status = YouTubePlaylistImport.ImportStatus.PENDING
    initiated_by = factory.SubFactory(InstructorFactory)


# ──────────────────────────────────────────────
# Enrollment factories
# ──────────────────────────────────────────────


class EnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrollment

    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    enrollment_status = Enrollment.EnrollmentStatus.ACTIVE
    is_active = True


class LessonProgressFactory(DjangoModelFactory):
    class Meta:
        model = LessonProgress

    enrollment = factory.SubFactory(EnrollmentFactory)
    student = factory.LazyAttribute(lambda obj: obj.enrollment.student)
    lesson = factory.SubFactory(LessonFactory)
    is_completed = False


class VideoProgressFactory(DjangoModelFactory):
    class Meta:
        model = VideoProgress

    student = factory.SubFactory(UserFactory)
    video = factory.SubFactory(VideoFactory)
    watch_time_seconds = 0
    last_position_seconds = 0
    is_completed = False


# ──────────────────────────────────────────────
# Quiz factories
# ──────────────────────────────────────────────


class QuizFactory(DjangoModelFactory):
    class Meta:
        model = Quiz

    course = factory.SubFactory(CourseFactory)
    lesson = factory.SubFactory(
        LessonFactory,
        lesson_type=Lesson.LessonType.QUIZ,
    )
    title = factory.Sequence(lambda n: f"Quiz {n}")
    description = factory.Faker("sentence", nb_words=8)
    time_limit_minutes = 30
    max_attempts = 3
    passing_score = 50
    shuffle_questions = False
    shuffle_options = False
    is_active = True
    order = factory.Sequence(lambda n: n)


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    quiz = factory.SubFactory(QuizFactory)
    question_text = factory.Faker("sentence", nb_words=10)
    question_type = Question.QuestionType.MCQ
    points = 1
    order = factory.Sequence(lambda n: n)
    explanation = factory.Faker("sentence", nb_words=6)


class OptionFactory(DjangoModelFactory):
    class Meta:
        model = Option

    question = factory.SubFactory(QuestionFactory)
    option_text = factory.Faker("sentence", nb_words=4)
    is_correct = False
    order = factory.Sequence(lambda n: n)


class QuizAttemptFactory(DjangoModelFactory):
    class Meta:
        model = QuizAttempt

    quiz = factory.SubFactory(QuizFactory)
    student = factory.SubFactory(UserFactory)
    attempt_number = 1
    total_points = 0
    total_questions = 0
    status = QuizAttempt.Status.IN_PROGRESS


class NotificationPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)
    email_notifications_enabled = True
    in_app_notifications_enabled = True
    course_updates = True
    assignment_notifications = True
    quiz_notifications = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = kwargs["user"]
        preference, _ = model_class.objects.get_or_create(user=user)
        for key, value in kwargs.items():
            if key != "user":
                setattr(preference, key, value)
        preference.save()
        return preference


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Notification {n}")
    message = factory.Faker("sentence", nb_words=10)
    notification_type = Notification.NotificationType.SYSTEM_ALERT
    is_read = False


class StudentAnswerFactory(DjangoModelFactory):
    class Meta:
        model = StudentAnswer

    attempt = factory.SubFactory(QuizAttemptFactory)
    question = factory.SubFactory(QuestionFactory)
    selected_option = factory.SubFactory(OptionFactory)
    is_correct = False


# ──────────────────────────────────────────────
# Assignment factories
# ──────────────────────────────────────────────


class AssignmentFactory(DjangoModelFactory):
    class Meta:
        model = Assignment

    course = factory.SubFactory(CourseFactory)
    lesson = factory.SubFactory(
        LessonFactory,
        lesson_type=Lesson.LessonType.ASSIGNMENT,
    )
    title = factory.Sequence(lambda n: f"Assignment {n}")
    description = factory.Faker("paragraph", nb_sentences=3)
    instructions = factory.Faker("paragraph", nb_sentences=5)
    max_score = 100
    submission_type = Assignment.SubmissionType.FILE_AND_TEXT
    allow_resubmission = True
    max_attempts = 3
    is_published = True
    order = factory.Sequence(lambda n: n)


class AssignmentSubmissionFactory(DjangoModelFactory):
    class Meta:
        model = AssignmentSubmission

    assignment = factory.SubFactory(AssignmentFactory)
    student = factory.SubFactory(UserFactory)
    submission_text = factory.Faker("paragraph", nb_sentences=2)
    file_url = "https://storage.example.com/submissions/file.pdf"
    attempt_number = 1
    status = AssignmentSubmission.Status.SUBMITTED
    submitted_at = factory.LazyFunction(lambda: __import__("django.utils.timezone", fromlist=["now"]).now())


class SubmissionFactory(AssignmentSubmissionFactory):
    pass


class AssignmentGradeFactory(DjangoModelFactory):
    class Meta:
        model = AssignmentGrade

    submission = factory.SubFactory(AssignmentSubmissionFactory)
    grader = factory.SubFactory(InstructorFactory)
    score = 85
    feedback = factory.Faker("paragraph", nb_sentences=2)
    graded_at = factory.LazyFunction(lambda: __import__("django.utils.timezone", fromlist=["now"]).now())


# ──────────────────────────────────────────────
# Review factories
# ──────────────────────────────────────────────


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    rating = 4
    review_text = factory.Faker("paragraph", nb_sentences=3)
    status = Review.Status.PUBLISHED


class ReviewResponseFactory(DjangoModelFactory):
    class Meta:
        model = ReviewResponse

    review = factory.SubFactory(ReviewFactory)
    instructor = factory.LazyAttribute(lambda obj: obj.review.course.instructor)
    response_text = factory.Faker("paragraph", nb_sentences=2)


# ──────────────────────────────────────────────
# Certificate factories
# ──────────────────────────────────────────────


class CertificateFactory(DjangoModelFactory):
    class Meta:
        model = Certificate

    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    certificate_number = factory.Sequence(lambda n: f"TBOS-2026-{n + 1:06d}")
    verification_code = factory.Sequence(lambda n: f"verify-code-{n + 1}")
    issue_date = factory.LazyFunction(lambda: __import__("django.utils.timezone", fromlist=["now"]).now().date())
    certificate_url = "https://tbos.com/api/v1/certificates/fake/download/"


# ──────────────────────────────────────────────
# Payment factories
# ──────────────────────────────────────────────


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(
        CourseFactory,
        is_free=False,
        price=120,
        discount_price=100,
        status="published",
    )
    order_number = factory.Sequence(lambda n: f"TBOS-ORDER-{n + 1:06d}")
    order_status = Order.OrderStatus.PENDING
    amount = factory.LazyAttribute(lambda obj: obj.course.effective_price)
    currency = "USD"
    payment_method = Order.PaymentMethod.STRIPE


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    payment_provider = Payment.Provider.STRIPE
    payment_status = Payment.PaymentStatus.PENDING
    transaction_id = ""
    payment_data = factory.LazyFunction(dict)


class BillingDetailsFactory(DjangoModelFactory):
    class Meta:
        model = BillingDetails

    user = factory.SubFactory(UserFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda obj: obj.user.email)
    country = "Bangladesh"
    city = "Dhaka"
    postal_code = "1207"
    address = factory.Faker("street_address")
    phone_number = "+8801700000000"
