
from django.contrib import admin
# imports all models
from .models import *
from django.utils.html import format_html
from django.contrib.admin.widgets import AdminFileWidget
from django.forms import ModelForm

# Move all TabularInline classes to the very top
class What_you_learn_TabularInline(admin.TabularInline):
    model = What_you_learn

class Requirements_TabularInline(admin.TabularInline):
    model = Requirements

class lesson_TabularInline(admin.TabularInline):
    model = Lesson

class Video_TabularInline(admin.TabularInline):
    model = Video

# Custom admin form for image preview
class ImagePreviewWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        if value and hasattr(value, 'url'):
            output += format_html('<br><img src="{}" style="max-width:200px; max-height:200px;" />', value.url)
        return output

# Course admin with image preview
class CourseAdminForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'featured_image': ImagePreviewWidget,
        }

class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    inlines = (What_you_learn_TabularInline, Requirements_TabularInline, lesson_TabularInline, Video_TabularInline)
    list_display = ('title', 'author', 'category', 'created_at')
    search_fields = ('title', 'author__name')
    list_filter = ('category', 'author')

# Custom admin form for image preview
class ImagePreviewWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        if value and hasattr(value, 'url'):
            output += format_html('<br><img src="{}" style="max-width:200px; max-height:200px;" />', value.url)
        return output

# Course admin with image preview
class CourseAdminForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'featured_image': ImagePreviewWidget,
        }

class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    inlines = (What_you_learn_TabularInline, Requirements_TabularInline, lesson_TabularInline, Video_TabularInline)
    list_display = ('title', 'author', 'category', 'created_at')
    search_fields = ('title', 'author__name')
    list_filter = ('category', 'author')
# Author admin with image preview
class AuthorAdminForm(ModelForm):
    class Meta:
        model = Author
        fields = '__all__'
        widgets = {
            'author_profile': ImagePreviewWidget,
        }

class AuthorAdmin(admin.ModelAdmin):
    form = AuthorAdminForm
    list_display = ('name', 'skill')
    search_fields = ('name', 'skill')

# Video admin with thumbnail preview
class VideoAdminForm(ModelForm):
    class Meta:
        model = Video
        fields = '__all__'
        widgets = {
            'thumbnail': ImagePreviewWidget,
        }

class VideoAdmin(admin.ModelAdmin):
    form = VideoAdminForm
    list_display = ('title', 'course', 'lesson')
    search_fields = ('title', 'course__title')

# Assignment admin with PDF preview
class AssignmentAdminForm(ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'
        widgets = {
            'pdf_file': AdminFileWidget,
        }

class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    list_display = ('course', 'title')
    search_fields = ('title',)

# Submission admin with file preview
class SubmissionAdminForm(ModelForm):
    class Meta:
        model = Submission
        fields = '__all__'
        widgets = {
            'file_upload': AdminFileWidget,
        }

class SubmissionAdmin(admin.ModelAdmin):
    form = SubmissionAdminForm
    list_display = ('assignment', 'student', 'status', 'grade', 'submitted_at')
    search_fields = ('student__username', 'assignment__title')
    list_filter = ('status',)


## Remove duplicate inline class definitions below
admin.site.register(Course, CourseAdmin)
admin.site.register(Categories)
admin.site.register(Author, AuthorAdmin)
admin.site.register(level)
admin.site.register(What_you_learn)
admin.site.register(Requirements)
admin.site.register(Lesson)
admin.site.register(Language)
admin.site.register(UserCourse)
admin.site.register(Payment)
admin.site.register(Review)

#++++++++++++++++++++++++++++++++ Quiz Registers ++++++++++++++++++++++++++++++++++++++++
from django.contrib import admin
from .models import Quiz, Question, Option, BillingDetails


class option_TabularInline(admin.TabularInline):
    model = Option
class question_admin(admin.ModelAdmin):
    inlines = (option_TabularInline,)

admin.site.register(Question,question_admin)
admin.site.register(Option)
admin.site.register(Quiz)
admin.site.register(UserRecord)
admin.site.register(UserAnswer)

# ++++++++++++++++++++++++++++++++ Assignment Registers ++++++++++++++++++++++++++++++++++
from .models import Assignment, Submission
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(BillingDetails)
admin.site.register(Submission, SubmissionAdmin)


