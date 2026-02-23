from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Count, Sum
from django.shortcuts import render, get_object_or_404,redirect
from django.utils.timezone import now

from django.template.loader import render_to_string
from django.http import JsonResponse,Http404
from django.contrib import messages
from django.utils import timezone
#import for payment
import stripe

from . import settings
from django.urls import reverse


from Utils_File.video_durations import video_duration

from app.models import Categories, Course, Author, level, UserCourse, Quiz, Assignment, Video, Payment, UserRecord, \
    Question, Option, UserAnswer, Submission,BillingDetails,Review




def BASE(request):
    return render(request,'base.html')


def HOME(request):
    category = Categories.objects.all().order_by("id")[0:5]

    # Get courses with aggregated data using direct model references
    courses = Course.objects.filter(status='PUBLISH').order_by('-id').annotate(
        avg_rating=Avg('review__course_rating'),  # Direct review relationship
        total_reviews=Count('review')  # Direct review count
    )

    # Get durations using your existing utility
    durations = video_duration(courses)

    # Add durations to course objects
    for course in courses:
        course.total_duration = durations.get(course.id, "0h 0m")
    instructor = Author.objects.all()
    users = User.objects.all()

    context = {
        'Category': category,
        'Courses': courses,
        'instructor': instructor,
        'users': users,

    }


    return render(request, 'Main/home.html', context)

def INSTRUCTOR(request,id):
    instructor = get_object_or_404(Author, id=id)
    courses = Course.objects.filter(author=id)
    context={
        'instructor':instructor,
        'courses':courses,

    }
    return render(request,'Instructor/instructor.html',context)


@login_required
def SINGLE_COURSE(request):
    # Get the category ID from the query parameters
    category_id = request.GET.get('category_id')

    # Base queryset with annotations using default relationships
    courses = Course.objects.annotate(
        avg_rating=Avg('review__course_rating'),  # Default reverse relation
        total_reviews=Count('review'),  # Default reverse relation
        total_lessons=Count('lesson')  # Default reverse relation
    )

    # Apply category filter if specified
    if category_id:
        courses = courses.filter(category_id=category_id)

    # Apply sorting
    sort_option = request.GET.get('sort', 'default')
    if sort_option == 'new':
        courses = courses.order_by('-created_at')
    elif sort_option == 'price_low_high':
        courses = courses.order_by('price')
    elif sort_option == 'price_high_low':
        courses = courses.order_by('-price')

    # Pagination
    paginator = Paginator(courses, 3)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    # Calculate durations for paginated courses
    durations = video_duration(page_obj.object_list)
    for course in page_obj.object_list:
        course.total_duration = video_duration(course)  # Directly assign the string value


    # Get other context data
    context = {
        "Category": Categories.objects.all(),
        "level": level.objects.all(),
        "Courses": page_obj,
        'Free_course_count': Course.objects.filter(price=0).count(),
        'Paid_course_count': Course.objects.filter(price__gte=1).count(),
        'sort_option': sort_option,
        'page_obj': page_obj,
    }
    return render(request, 'Main/single_course.html', context)

def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')

    # Base queryset
    if price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif price == ['PriceAll']:
        course = Course.objects.all()
    elif category:
        course = Course.objects.filter(category_id__in=category)
    elif level:
        course = Course.objects.filter(level_id__in=level)
    else:
        course = Course.objects.all()

    # Add annotations
    course = course.annotate(
        avg_rating=Avg('review__course_rating'),
        total_reviews=Count('review'),
        total_lessons=Count('lesson')
    ).order_by('-id')

    # Calculate durations
    durations = video_duration(course)
    for c in course:
        c.total_duration = durations.get(c.id, "0h 0m")  # Fix here



    context = {
        'Courses': course,
    }

    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data': t})

def CONTACT_US(request):
    category=Categories.get_all_category(Categories)
    context={
        "Category":category,
    }
    return render(request,'Main/contact_us.html',context)


def ABOUT_US(request):
    # get all cat from db
    category = Categories.objects.all().order_by("id")[0:5]

    # get courses from db
    course = Course.objects.filter(status='PUBLISH').order_by('-id')

    instructor = Author.objects.all()

    users = User.objects.all()

    # create context name dic
    context = {
        'Category': category,
        'Courses': course,
        'instructor': instructor,
        'users': users,

    }

    return render(request,'Main/about_us.html',context)


def SEARCH_COURSES(request):
    category=Categories.get_all_category(Categories)
    query=request.GET['query']
    course=Course.objects.filter(title__icontains=query)
    context={
        "Courses":course,
        "Category": category,
    }
    return render(request,"search/search_courses.html",context)


@login_required
def COURSE_DETAILS(request, slug):
    # Get the course or return a 404
    course = get_object_or_404(Course, slug=slug)
    author = course.author  # Get the course author

    # Handle review submission
    if request.method == 'POST':
        content = request.POST.get('content')
        course_rating = request.POST.get('course_rating')
        instructor_rating = request.POST.get('author_rating')

        Review.objects.create(
            user=request.user,
            course=course,
            content=content,
            course_rating=course_rating,
            instructor_rating=instructor_rating
        )
        return redirect('course_details', slug=slug)

    # Existing code
    category = Categories.objects.all()
    time_duration = video_duration(course)
    enroll_status = UserCourse.objects.filter(user=request.user, course=course).first() if request.user.is_authenticated else None
    related_courses = Course.objects.filter(category=course.category).exclude(id=course.id)
    latest_courses = Course.objects.filter(status="PUBLISH").order_by('-created_at')[:4]
    quizzes = Quiz.objects.filter(course=course)
    assignments = Assignment.objects.filter(course=course)

    # Reviews and ratings logic
    reviews = Review.objects.filter(course=course).select_related('user')

    # Calculate course-specific ratings
    course_avg = reviews.aggregate(Avg('course_rating'))['course_rating__avg'] or 0
    instructor_avg = reviews.aggregate(Avg('instructor_rating'))['instructor_rating__avg'] or 0

    # Calculate rating distribution
    course_distribution = reviews.values('course_rating').annotate(count=Count('course_rating'))
    instructor_distribution = reviews.values('instructor_rating').annotate(count=Count('instructor_rating'))

    # Convert distributions to dictionaries
    course_dist_dict = {d['course_rating']: d['count'] for d in course_distribution}
    instructor_dist_dict = {d['instructor_rating']: d['count'] for d in instructor_distribution}

    # Calculate instructor statistics
    author_courses = Course.objects.filter(author=author)
    instructor_stats = {
        'avg_rating': round(Review.objects.filter(course__in=author_courses).aggregate(
            Avg('instructor_rating'))['instructor_rating__avg'] or 0.0, 1),
        'total_reviews': Review.objects.filter(course__in=author_courses).count(),
        'total_students': UserCourse.objects.filter(course__in=author_courses).values('user').distinct().count(),
        'total_courses': author_courses.count()
    }

    context = {
        "course": course,
        "category": category,
        "time_duration": time_duration,
        "enroll_status": enroll_status,
        "related_courses": related_courses,
        "latest_courses": latest_courses,
        "quizzes": quizzes,
        "assignments": assignments,
        "reviews": reviews,
        "course_avg": round(course_avg, 2),
        "instructor_avg": round(instructor_avg, 2),
        "course_distribution": course_dist_dict,
        "instructor_distribution": instructor_dist_dict,
        "instructor_stats": instructor_stats  # Add instructor stats to context
    }

    return render(request, 'course/course_details.html', context)
@login_required
def WATCH_COURSE(request, slug):
    lecture = request.GET.get('lecture')  # Get the 'lecture' parameter from URL
    if not lecture:
        return redirect('404')  # Redirect if lecture parameter is missing

    try:
        # Fetch course based on slug
        course_id = Course.objects.get(slug=slug)
        course = Course.objects.filter(slug=slug)

        # Check if user is enrolled (with better error handling)
        try:
            check_enroll = UserCourse.objects.get(user=request.user, course=course_id)
        except UserCourse.DoesNotExist:
            # If the user is not enrolled, raise a more descriptive error
            return redirect('404')  # Or show a message that the user is not enrolled

        # Fetch the video object safely
        try:
            video = Video.objects.get(id=lecture)
        except Video.DoesNotExist:
            raise Http404("Video does not exist")

        if course.exists():
            course = course.first()
        else:
            return redirect('404')

    except (Course.DoesNotExist):
        return redirect('404')

    # Prepare the context
    context = {
        'course': course,
        'video': video,
        'lecture': lecture,
    }
    return render(request, 'course/watch_course.html', context)


def PAGE_NOT_FOUND(request):
    category=Categories.get_all_category(Categories)
    context={
        "Category":category,
    }
    return render(request,'errors/404.html',context)




stripe.api_key = settings.STRIPE_SECRET_KEY

def CHECKOUT(request, slug):
    course = get_object_or_404(Course, slug=slug)
    action = request.GET.get('action')

    # If the course is free, enroll the user directly
    if course.price == 0:
        usercourse = UserCourse(
            user=request.user,
            course=course
        )
        usercourse.save()
        messages.success(request, "Course is successfully enrolled!")
        return redirect('my_course')

    # If the action is 'create_payment', process the payment
    elif action == 'create_payment':
        if request.method == 'POST':
            try:
                # Retrieve form data
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                country = request.POST.get('country')
                address1 = request.POST.get('address1')
                city = request.POST.get('city')
                postcode = request.POST.get('postcode')
                phone = request.POST.get('phone')
                email = request.POST.get('email')
                order_comments = request.POST.get('order_comments', '')

                # Validate required fields
                if not all([first_name, last_name, country, address1, city, postcode, phone, email]):
                    messages.error(request, "Please fill out all required fields.")
                    return redirect('checkout', slug=slug)

                # Save billing details to the database
                billing = BillingDetails.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address1,
                    city=city,
                    country=country,
                    postcode=postcode,
                    phone=phone,
                )
                # Ensure `course.discount` is a single value (not a tuple)
                discount_percentage = course.discount    # Convert to float if needed

                # Calculate discount factor using Decimal arithmetic
                discount_factor = discount_percentage / Decimal('100')
                final_amount = course.price - (course.price * discount_factor)

                # Ensure amount is at least 1 cent
                final_amount = max(final_amount, Decimal('0.01'))
                # Create a Stripe Checkout Session
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    # Calculate final price after discount

                    line_items=[
                        {
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': course.title,
                                },
                                'unit_amount': int(final_amount * 100),  # Convert to cents
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=request.build_absolute_uri(
                        reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri(reverse('payment_failed')),
                    metadata={
                        'course_id': course.id,
                        'user_id': request.user.id,
                    },
                )
                return redirect(checkout_session.url)
            except Exception as e:
                messages.error(request, f"Payment failed: {str(e)}")
                return redirect('checkout', slug=slug)

    # Default context for GET requests
    context = {
        'course': course,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'checkout/checkout.html', context)
def payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            # Retrieve the Stripe session
            session = stripe.checkout.Session.retrieve(session_id)

            # Get course and user details from session metadata
            course_id = session.metadata.get('course_id')
            user_id = session.metadata.get('user_id')

            course = Course.objects.get(id=course_id)
            user = User.objects.get(id=user_id)

            # Calculate the final amount after discount (if any)
            final_amount = course.price - (course.price * course.discount / 100)

            # Retrieve the latest billing details for the user
            billing = BillingDetails.objects.filter(user=user).latest('id')

            # Save payment details to the database
            payment = Payment.objects.create(
                user=user,
                course=course,
                payment_id=session.payment_intent,
                status=True,
                amount=final_amount,
                billing_details=billing,  # Link billing details to the payment
            )

            # Enroll the user in the course
            UserCourse.objects.create(user=user, course=course, paid=True)

            # Generate the course_details URL with the course slug
            course_details_url = request.build_absolute_uri(
                reverse('course_details', kwargs={'slug': course.slug})
            )

            # Send email notification
            subject = f"Enrollment Confirmation for {course.title}"
            message = f"""
                Hi {user.first_name},

                Thank you for enrolling in the course "{course.title}".

                You can now access the course here: {course_details_url}

                Billing Details:
                - Name: {billing.first_name} {billing.last_name}
                - Email: {billing.email}
                - Address: {billing.address}, {billing.city}, {billing.country}, {billing.postcode}
                - Phone: {billing.phone}

                Best regards,
                Your Course Team
            """
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            # Show success message
            messages.success(request, "Payment successful! You are now enrolled in the course.")
            return redirect('my_course')
        except Exception as e:
            # Log the error and show a failed message
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('home')
    else:
        # Invalid session ID
        messages.error(request, "Invalid session ID. Please try again.")
        return redirect('home')

def payment_failed(request):
    # Show a failed message
    messages.error(request, "Payment failed. Please try again.")
    return redirect('home')

@login_required
def MY_COURSES(request):
    # Fetch all user courses
    courses = UserCourse.objects.filter(user=request.user)
    queryset = [q_courses.course for q_courses in courses]
    time_duration=video_duration(queryset)


    # Fetch all categories related to user courses
    categories = Categories.objects.filter(course__usercourse__user=request.user).distinct()

    # Get selected category from request
    selected_category = request.GET.get('category')

    # Filter courses based on the selected category
    if selected_category and selected_category != "All Categories":
        courses = courses.filter(course__category__name=selected_category)

    # Get sorting option from the request (ensure a default value)
    sort_option = request.GET.get('sort', 'default')

    # Sorting logic
    if sort_option == 'new':
        courses = courses.order_by('-course__created_at')  # Sort by newest
    elif sort_option == 'price_low_high':
        courses = courses.order_by('course__price')  # Sort by price (low to high)
    elif sort_option == 'price_high_low':
        courses = courses.order_by('-course__price')  # Sort by price (high to low)
#============================== paginatinos ==========================

    # Pagination logic (for "Load More")
    default_limit = 3  # Initial number of courses to show
    limit = int(request.GET.get('limit', default_limit))  # Get the current limit from the request
    courses = courses[:limit]  # Limit courses to the current limit

    # Check if there are more courses to load
    has_more = len(UserCourse.objects.filter(user=request.user)) > limit



    context = {
        "course": courses,
        "categories": categories,
        "selected_category": selected_category,  # To retain the selected category
        "sort_option": sort_option,  # Retain the selected sort option
        "limit": limit,
        "has_more": has_more,  # Whether there are more courses to load
        "time_duration":time_duration,
    }
    return render(request, "course/My_Course.html", context)


def SEARCH_ENROL_COURSES(request):
    category = Categories.get_all_category(Categories)
    query = request.GET['query']
    enrol_course = UserCourse.objects.filter(course__title__icontains=query)
    context = {
        "Enrol_course":enrol_course,
        "Category": category,
    }
    return render(request, "search/Search_Enrol_Course.html", context)
def shop_order_completed(request):
    return render(request, 'checkout/shop-order-completed.html')




#++++++++++++++++++++++++++++++++++++++ quizez ++++++++++++++++++++++++++++++++++
@login_required
def quiz_confirmation(request, quiz_id):
    # Fetch the quiz object
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Fetch or create a user record
    user_record, created = UserRecord.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        defaults={
            'score': 0,
            'total_questions': quiz.question_set.count(),
            'correct_answers': 0,
            'attempts_left': quiz.max_attempts,
        }
    )

    # Check if no attempts are left
    if user_record.attempts_left <= 0:
        return redirect('quiz_result', user_record.id)

    # Prepare context data
    context = {
        'quiz': quiz,
        'attempts_left': user_record.attempts_left,
        'time_limit': quiz.time_limit,  # Time limit for the quiz (in minutes)
        'user_record': user_record,
    }

    # Render the confirmation template
    return render(request, 'Quizes/quiz_confirmation.html', context)


@login_required
def quiz_start(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.question_set.all()
    total_questions = questions.count()

    # Retrieve or create user record for this quiz
    user_record, created = UserRecord.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        defaults={
            'total_questions': total_questions,
            'attempts_left': quiz.max_attempts,
            'score': 0,  # Initialize score to 0
            'start_time': timezone.now(),
        }
    )

    # Handle if no attempts are left
    if user_record.attempts_left <= 0:
        return redirect('quiz_result', user_record.id)

    # Handle POST request (saving answers)
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        option_id = request.POST.get('option_id')
        question = get_object_or_404(Question, id=question_id)

        # Handle timer expiration (no option selected)
        if option_id:
            option = get_object_or_404(Option, id=option_id)
            is_correct = option.is_correct
        else:
            # Treat the question as incorrect if no option was selected due to timeout
            is_correct = False

        # Save the user's answer
        UserAnswer.objects.create(
            user_record=user_record,
            question=question,
            selected_option=None if not option_id else option,
            is_correct=is_correct
        )

        # Update the correct answers count
        user_record.correct_answers = UserAnswer.objects.filter(
            user_record=user_record, is_correct=True).count()
        user_record.save()


        # Get the next unanswered question
        next_question = Question.objects.filter(quiz=quiz).exclude(
            id__in=user_record.answers.values_list('question__id', flat=True)).first()

        # If no unanswered questions, the quiz is finished
        if not next_question:
            # Quiz is completed, save the final score and decrement attempts left
            user_record.score = user_record.correct_answers
            user_record.end_time = timezone.now()

            # Update highest score if this attempt is better than the previous one
            if user_record.score > user_record.highest_score:
                user_record.highest_score = user_record.score

            user_record.attempts_left -= 1
            user_record.save()
            # If there are remaining attempts, allow the user to retake the quiz
            if user_record.attempts_left > 0:
                return redirect('quiz_start', quiz_id=quiz.id)

            return redirect('quiz_result', user_record.id)

        # Redirect to the next question
        return redirect('quiz_start', quiz_id=quiz.id)

    # Get the current question to display
    current_question = Question.objects.filter(quiz=quiz).exclude(
        id__in=user_record.answers.values_list('question__id', flat=True)).first()

    # If no question is found (quiz completed), redirect to results
    if not current_question:
        return redirect('quiz_result', user_record.id)

    # Calculate the elapsed time and remaining time
    elapsed_time = timezone.now() - user_record.start_time
    time_left = quiz.time_limit * 60 - int(elapsed_time.total_seconds())  # Time left in seconds

    # Calculate progress
    progress = (user_record.answers.count() / user_record.total_questions) * 100 if user_record.total_questions else 0

    context = {
        'quiz': quiz,
        'user_record': user_record,
        'current_question': current_question,
        'progress': progress,
        'time_limit': quiz.time_limit,  # Send time limit in minutes
        'time_left': time_left,  # Send remaining time in seconds
        "total_questions": total_questions,
    }

    return render(request, 'Quizes/quiz_start.html', context)


# Result Page to show the correct answers and score
@login_required
def quiz_result(request, record_id):
    user_record = get_object_or_404(UserRecord, id=record_id, user=request.user)
    quiz = user_record.quiz

    # Fetch all questions and corresponding user answers
    questions = Question.objects.filter(quiz=quiz)
    user_answers = UserAnswer.objects.filter(user_record=user_record)

    # Prepare context with questions, user answers, and correct answers
    question_data = []
    for question in questions:
        user_answer = user_answers.filter(question=question).first()
        correct_option = question.options.filter(is_correct=True).first()
        question_data.append({
            'question': question.text,
            'user_answer': user_answer.selected_option if user_answer else None,
            'correct_option': correct_option,
            'is_correct': user_answer.is_correct if user_answer else False,
        })

    # Calculate the percentage score
    percentage_score = (user_record.score / user_record.total_questions) * 100
    pass_fail = 'Pass' if percentage_score >= 75 else 'Fail'

    context = {
        'user_record': user_record,
        'quiz': user_record.quiz,
        'highest_score': user_record.highest_score,
        'score': user_record.score,  # This is the score of the current attempt
        'correct_answers': user_record.correct_answers,
        'total_questions': user_record.total_questions,
        'attempts_left': user_record.attempts_left,
        'percentage_score': percentage_score,
        'pass_fail': pass_fail,  # Pass or Fail
        'question_data': question_data,
    }

    return render(request, 'Quizes/quiz_result.html', context)


#+++++++++++++++++++++++++++++++++++ Assignment ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@login_required
def confirmation_assessment(request, assignment_id):
    # Get the assignment or raise 404 if not found
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Try to get the submission, or create one if it doesn't exist
    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=request.user,
        defaults={
            'status': 'Pending',
            'start_time': int(now().timestamp()),
        }
    )

    # Check if the submission has already been submitted
    if submission.status.lower() == "submitted":
        messages.info(request, "You have already submitted this assignment.")
        return redirect('view_grading', assignment_id=assignment.id)

    # Pass assignment and submission to the context
    context = {
        'assignment': assignment,
        'submission': submission,
    }
    return render(request, 'Assignments/confirm_assignment.html', context)
@login_required
def start_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Get or create a submission for the student
    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=request.user,
        defaults={"status": "in_progress", "start_time": int(now().timestamp())}  # Save the start time as a timestamp
    )

    if not created and submission.start_time is None:
        submission.start_time = int(now().timestamp())  # Set start time if not already set
        submission.save()

    # Calculate remaining time
    elapsed_time = int(now().timestamp()) - submission.start_time  # Time elapsed since the assignment was started
    remaining_time = max(assignment.time_limit * 60 - elapsed_time, 0)  # Convert time_limit to seconds

    # Handle form submission (both manual and automatic)
    if request.method == 'POST':
        submission_text = request.POST.get('submission_text', submission.submission_text)
        file_upload = request.FILES.get('file_upload')

        # If there is new submission text or a file, update them
        if submission_text:
            submission.submission_text = submission_text
        if file_upload:
            submission.file_upload = file_upload

        submission.status = "submitted"
        submission.submitted_at = now()
        submission.save()

        return redirect('view_grading', assignment_id=assignment.id)

    # Check if time is up and automatically save the content if there's any text
    if remaining_time == 0:
        # If there is any content in the text area, save it
        submission_text = request.POST.get('submission_text', submission.submission_text)
        file_upload = request.FILES.get('file_upload')

        # If there's new submission text or file, update them
        if submission_text:
            submission.submission_text = submission_text
        if file_upload:
            submission.file_upload = file_upload

        submission.status = "submitted"
        submission.submitted_at = now()
        submission.save()

    context = {
        'assignment': assignment,
        'submission': submission,
        'remaining_time': remaining_time,  # Pass remaining time to the template
    }
    return render(request, 'Assignments/start_assignment.html', context)



@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = get_object_or_404(Submission, assignment=assignment, student=request.user)

    if request.method == 'POST':
        # Process submission
        submission.submission_text = request.POST.get('submission_text', submission.submission_text)
        file_upload = request.FILES.get('file_upload')
        if file_upload:
            submission.file_upload = file_upload

        submission.status = "submitted"
        submission.submitted_at = timezone.now()
        submission.save()
        return redirect('view_grading', assignment_id=assignment.id)

    return JsonResponse({"status": "error", "message": "Invalid request"})


@login_required
def view_grading(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = get_object_or_404(
        Submission,
        assignment=assignment,
        student=request.user
    )

    file_upload = None
    if submission.file_upload:
        file_upload = {
            'url': submission.file_upload.url,
            'name': submission.file_upload.name.split('/')[-1],
            'size': submission.file_upload.size
        }

    context = {
        'assignment': assignment,
        'submission': {
            'student': submission.student.get_full_name(),
            'assignment': assignment.title,
            'grade': submission.grade or "Not Graded",
            # Get human-readable status using get_status_display()
            'status': submission.get_status_display(),
            'submission_text': submission.submission_text,
            'file_upload': file_upload,
            'submitted_at': submission.submitted_at
        }
    }
    return render(request, 'Assignments/view_grading.html', context)

def success():
    return None


def error():
    return None