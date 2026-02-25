from datetime import timedelta

from django.db.models import Count, Avg
from django.utils.timezone import now
import time

def get_current_timestamp():
    return int(time.time())

from django.db import models

# import for course slug
from django.utils.text import slugify
from django.db.models.signals import pre_save
# import user
from django.contrib.auth.models import User

from django.contrib.auth.models import User
from django.db import models
from Utils_File.parse_and_save_aiken import parse_and_save_aiken


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='Media/User_avatars/', null=True, blank=True)

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

# Create your models here.
class Categories(models.Model):
    icon=models.CharField(max_length=200,null=True)
    name=models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def get_all_category(self):
        return  Categories.objects.all().order_by("id")

class Author(models.Model):
    author_profile = models.ImageField(upload_to="Media/author")
    name = models.CharField(max_length=100, null=True)
    skill=models.CharField(max_length=100, null=True)
    about_author = models.TextField()
    linkedin = models.URLField(max_length=200, blank=True, null=True)
    twitter = models.URLField(max_length=200, blank=True, null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)


    def __str__(self):
        return self.name


class level(models.Model):
    name=models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Language(models.Model):
        language = models.CharField(max_length=100)

        def __str__(self):
            return self.language

class Course(models.Model):
    STATUS = (
        ('PUBLISH', 'PUBLISH'),
        ('DRAFT', 'DRAFT'),
    )

    featured_image = models.ImageField(upload_to="Media/featured_img", null=True)
    featured_video = models.CharField(max_length=300, null=True)
    title = models.CharField(max_length=500)
    created_at = models.DateField(auto_now_add=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True,related_name='+')
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    description = models.TextField()
    level=models.ForeignKey(level,on_delete=models.CASCADE,null=True )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00  # Add default for price
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00  # Add default for discount
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE, null=True)
    Deadline = models.CharField(max_length=100, null=True)
    slug = models.SlugField(default='', max_length=500, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=100, null=True)
    Certificate= models.CharField(null=True,max_length=100)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    def __str__(self):
        return self.title

    # get urls of course
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("course_details", kwargs={"slug": self.slug})

# write code for course slug
def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Course.objects.filter(slug=slug).order_by('-id')
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug

def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)

pre_save.connect(pre_save_post_receiver, Course)

# create model
class What_you_learn(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    points=models.CharField(max_length=500)

    def __str__(self):
        return self.points

#create model
class Requirements(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    points = models.CharField(max_length=500)

    def __str__(self):
        return self.points



class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    has_quizzes = models.BooleanField(default=False,null=True,blank=True)

    def __str__(self):
        return self.name + " - " + self.course.title


class Video(models.Model):
    serial_number = models.IntegerField(null=True)
    thumbnail = models.ImageField(upload_to="Media/Yt_Thumbnail", null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    youtube_id = models.CharField(max_length=200)
    time_duration = models.PositiveIntegerField(  # Should store minutes
        help_text="Duration in minutes",
        default=0)
    preview = models.BooleanField(default=False)

    def __str__(self):
        return self.title




class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    paid = models.BooleanField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " - " + self.course.title


#--------------------------- Billing details and payment -----------------------------------
class BillingDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20,default=1234)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Payment(models.Model):
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    billing_details = models.ForeignKey(BillingDetails, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} -- {self.course.title}"


# =========================== Review and Rating ==========================
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()
    course_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    instructor_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

#++++++++++++++++++++++++++++++++++++++++++ Quizzez Models +++++++++++++++++++++++++++++++++++++++++++++


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, related_name='quiz_set', on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    time_limit = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(default=1)
    quiz_file = models.FileField(upload_to='Media/quiz_files/', null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the instance first

        if self.quiz_file:
            from Utils_File.parse_and_save_aiken import parse_and_save_aiken
            parse_and_save_aiken(self.quiz_file.path, self)  # Pass correct arguments


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()

    def __str__(self):
        # Check if text exists, if not, return a default string
        return self.text if self.text else f"Question {self.id} (No text)"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)


class UserRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_records")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="user_records")
    score = models.IntegerField(default=0)
    highest_score = models.IntegerField(default=0)  # Store the highest score
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(null=True, blank=True)
    attempts_left=models.IntegerField(default=2)
    current_question_index = models.IntegerField(default=0)  # Add this field to track the question index
    def __str__(self):
        return f"Quiz: {self.quiz.title} | User: {self.user.username} | Score: {self.score}"

class UserAnswer(models.Model):
    user_record = models.ForeignKey(UserRecord, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers")
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField()

    def __str__(self):
        question_text = self.question.text if self.question else "No question"
        selected_option_text = self.selected_option.text if self.selected_option else "No option selected"
        return f"Question: {question_text} | Selected: {selected_option_text} | Correct: {self.is_correct}"


#+++++++++++++++++++++++++++++++++++++++++++++ Assignment moduls ++++++++++++++++++++++++++++++++++++++
from django.db import models
from django.contrib.auth.models import User

def due_time_limit():
    return now() + timedelta(days=60)

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True,blank=True)
    lesson_name = models.ForeignKey(Lesson, related_name='assignment_set', on_delete=models.CASCADE,blank=True,null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    pdf_file = models.FileField(upload_to='Media/assignments/pdfs/', null=True, blank=True)
    time_limit = models.IntegerField(default=60)

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late'),
        ('missing', 'Missing'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_text = models.TextField(null=True, blank=True)
    file_upload = models.FileField(upload_to='Media/submissions/', null=True, blank=True)
    grade = models.CharField(max_length=10, default="Pending")
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending"
    )
    submitted_at = models.DateTimeField(auto_now=True)
    start_time = models.IntegerField(default=get_current_timestamp, null=True, blank=True)
    end_time = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Submission by {self.student} for {self.assignment.title}"

__all__ = ['Categories','Submission','level','Lesson','Course','UserCourse','UserAnswer','UserRecord','Question','Author','User','Quiz','Language','Requirements','What_you_learn','Video','Review','Assignment','Payment','Option']