
from django.contrib import admin

#imports all models
from .models import *
# Register your models here.

class What_you_learn_TabularInline(admin.TabularInline):
    model = What_you_learn

class Requirements_TabularInline(admin.TabularInline):
    model = Requirements

class Video_TabularInline(admin.TabularInline):
    model = Video

class lesson_TabularInline(admin.TabularInline):
        model = Lesson
class course_admin(admin.ModelAdmin):
    inlines = (What_you_learn_TabularInline,Requirements_TabularInline,lesson_TabularInline,Video_TabularInline)




admin.site.register(Course,course_admin)
admin.site.register(Categories)
admin.site.register(Author)
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

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'title')
    search_fields = ('title',)

admin.site.register(BillingDetails)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'grade', 'submitted_at')
    search_fields = ('student__username', 'assignment__title')
    list_filter = ('status',)


