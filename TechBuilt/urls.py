from django.contrib import admin
from django.urls import path,include
from . import views,user_login
from django.contrib.auth import views as auth_views

#import media setting
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('base/',views.BASE,name='base'),
    path('404',views.PAGE_NOT_FOUND,name='404'),

    path('',views.HOME,name='home'),
    path('courses',views.SINGLE_COURSE,name='single_course'),
    path('course/filter-data', views.filter_data, name="filter-data"),
    path('course/<slug:slug>', views.COURSE_DETAILS, name="course_details"),


    path('Search_all_Course', views.SEARCH_COURSES, name="search_courses"),

    path('contact', views.CONTACT_US, name='contact_us'),
    path('about', views.ABOUT_US, name='about_us'),
    path('accounts/register',user_login.REGISTER, name='register'),

    #urls for login
    path('accounts/',include('django.contrib.auth.urls')),
    #url for logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dologin',user_login.DOLOGIN,name='dologin'),

    #urls for profile
    path("accounts/profile",user_login.PROFILE, name='Profile'),
	path("accounts/profile/update",user_login.PROFILE_UPDATE,name="Profile_update"),


    #url for my_courses
    path("my_course",views.MY_COURSES,name="my_course"),
    path('Search_Enrol_Course', views.SEARCH_ENROL_COURSES, name="Search_Enrol_Course"),

    path('course/watch_course/<slug:slug>',views.WATCH_COURSE,name="watch_course"),
    #======================instructor========================
    path('instructor/<int:id>',views.INSTRUCTOR,name="instructor"),

    #+++++++++++++++++++++++ quizez +++++++++++++++++

                  # Path for confirmation page to start the quiz
                  path('quiz_confirmation/<int:quiz_id>/', views.quiz_confirmation, name='quiz_confirmation'),

                  # Path for quiz UI (showing questions, options, and timer)
                  path('quiz_start/<int:quiz_id>/', views.quiz_start, name='quiz_start'),

                  # Path for result page to display score and correct answers
                  path('result/<int:record_id>/', views.quiz_result, name='quiz_result'),

    #++++++++++++++++++++++++++++++ assignment paths +++++++++++++++++++++++
                  path('assignment/<int:assignment_id>/confirm/', views.confirmation_assessment,name='confirmation_assessment'),
                  path('assignment/<int:assignment_id>/start/', views.start_assignment, name='start_assignment'),
                  path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
                  path('assignment/<int:assignment_id>/grading/', views.view_grading, name='view_grading'),             # View grading

                  # create urls for chackout
        path("checkout/<slug:slug>", views.CHECKOUT, name="checkout"),
        path('payment/success/', views.payment_success, name='payment_success'),
        path('payment/failed/', views.payment_failed, name='payment_failed'),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

