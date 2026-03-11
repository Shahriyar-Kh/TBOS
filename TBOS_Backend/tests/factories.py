import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import Profile, User
from apps.courses.models import Category, Course, Language, LearningOutcome, Level, Requirement
from apps.lessons.models import CourseSection, Lesson
from apps.videos.models import Video, YouTubePlaylistImport


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = User.Role.STUDENT
    is_active = True
    is_verified = False
    google_account = False
    password = factory.PostGenerationMethodCall("set_password", "StrongPass123!")


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
