# TechBuilt Open School — Modern Django LMS

A lightweight, production-ready online course platform (LMS) built with Django. TechBuilt Open School provides course publishing, video lessons, quizzes (Aiken import), assignments, Stripe payments, and an email-backed authentication flow.

## 🚀 Project Overview

TechBuilt Open School is a Django-based learning platform that enables instructors to publish courses and students to enroll, watch video lessons, take quizzes, and submit assignments. The project is implemented as a monolithic Django application using server-side rendered templates and conventional Django patterns.

This README is based entirely on the repository code (no assumptions). It documents the system architecture, features, data model, and developer setup.

## ✨ Key Features (Implemented)

- User features
  - Email-based authentication (login by email) using a custom backend (`app/Custom_EmailBackend.py`).
  - Registration, profile view and update flows (`TechBuilt/user_login.py`).
  - Course browsing and filtering with pagination and duration display (`TechBuilt/views.py`, `Utils_File/video_durations.py`).
  - Course details with instructor stats, reviews and ratings (`app/models.py`, `TechBuilt/views.py`).
  - Enroll / My courses — free-course auto-enroll and paid via Stripe Checkout (`TechBuilt/views.py`).
  - Watch course videos (access controlled by enrollment) — `Video` model and `WATCH_COURSE` view.

- Learning content
  - Courses, Lessons, Videos, Author profiles, Categories, Requirements, What-you-learn items (`app/models.py`).
  - Quizzes: `Quiz`, `Question`, `Option`, `UserRecord`, `UserAnswer` models. Quizzes can be imported from Aiken-format files via `Utils_File/parse_and_save_aiken.py` (the `Quiz.save()` hook triggers parsing if `quiz_file` is set).
  - Assignments and Submissions with statuses and grading fields.

- Payments & Billing
  - Stripe Checkout integration for paid courses (`TechBuilt/views.py`).
  - BillingDetails and Payment models to persist payment and billing info.
  - Email notification on successful payment using SMTP settings.

- Admin & System
  - Django Admin enabled (default).
  - Template-driven UI under `templates/` and static assets in `static/` & `staticfiles/`.

## 🏗️ Architecture Overview

- Web framework: Django (server-rendered templates)
- Monolith layout:
  - `TechBuilt/` — project settings, URLs, views for public pages and auth flows
  - `app/` — core application models, admin, and auxiliary utilities
  - `templates/` — page templates (home, course, quizzes, checkout, registration, etc.)
  - `static/` / `staticfiles/` — CSS/JS and vendor libraries
  - `Utils_File/` — parsing and utilities (quiz Aiken parser, video duration helper)
- Database: SQLite (configured in `TechBuilt/settings.py`) for development
- Payments: Stripe Checkout (server-side calls in views)
- Email: SMTP via credentials loaded from `.env` using `python-dotenv`/`load_dotenv` in settings

## 🧠 Tech Stack

- Backend: Python 3.10+ with Django 5.1.3
- Libraries (selected): `stripe`, `python-dotenv`, `django-crispy-forms` (see `requirements.txt`)
- Database: SQLite (development); recommended to use PostgreSQL in production
- Templating: Django templates
- Static assets: Bootstrap + custom CSS/JS in `static/` and `staticfiles/`

## 📊 Data Model (high level)

Core models defined in `app/models.py`:
- `Profile` — user avatar linked to Django `User`.
- `Categories`, `Author`, `level`, `Language` — supporting taxonomy.
- `Course` — course metadata, price, discount, slug generation
- `What_you_learn`, `Requirements`, `Lesson`, `Video` — course content structure
- `UserCourse` — enrollment and paid flag
- `BillingDetails`, `Payment` — payment capture and storage
- `Review` — course/instructor ratings and text review
- `Quiz`, `Question`, `Option`, `UserRecord`, `UserAnswer` — quiz engine and user attempts
- `Assignment`, `Submission` — assignment flow and grading

## 🔐 Authentication & Security Highlights

- Custom email authentication backend: `app/Custom_EmailBackend.py` allows logging in using email.
- Django standard password validators are enabled in `settings.py`.
- CSRF protection and session middleware are enabled (default in settings).
- Sensitive credentials are loaded from `.env` (e.g., `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`). Do NOT commit secrets.

Note: `DEBUG = True` in the repository; switch to `False` in production and set `ALLOWED_HOSTS` appropriately.

## ⚡ Performance & Scalability Notes

- Current setup is a single-process Django app with SQLite (development). For scale:
  - Replace SQLite with PostgreSQL.
  - Serve static files via CDN or web server (Nginx) after running `collectstatic`.
  - Run Django behind a WSGI server (Gunicorn/Uvicorn + Nginx) and enable connection pooling.
  - Offload long-running tasks (if introduced) to a task queue (Celery/RQ).

## 🛠️ Local Development Setup

1. Clone the repository (already in your workspace) and create a virtual environment:

```bash
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
# or cmd
venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file at the project root with at least the email credentials and (optionally) Stripe keys:

```
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
# Optionally (set in settings.py or env):
# STRIPE_PUBLISHABLE_KEY=pk_live_...
# STRIPE_SECRET_KEY=sk_live_...
```

4. Apply migrations and create a superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Run the dev server:

```bash
python manage.py runserver
```

6. Visit http://127.0.0.1:8000/ to access the site, and /admin (note: in code `admin` URL path is set to `/admin`).

## 🚀 Deployment (current repo evidence + recommendations)

The codebase does not include Docker or CI configuration. The repository uses Django's WSGI app (`TechBuilt/wsgi.py`). Typical production deployment steps:

- Use PostgreSQL in `DATABASES` and configure `DATABASE_URL` or settings.
- Set `DEBUG = False` and set `ALLOWED_HOSTS`.
- Configure environment variables for email and Stripe keys.
- Configure static serving: run `python manage.py collectstatic` and serve `STATIC_ROOT` from Nginx or cloud storage.
- Use Gunicorn/Uvicorn with Nginx as reverse proxy.

## 🔄 System Flow (user journey)

1. Visitor browses home / courses.
2. Visitor registers or logs in (login by email supported).
3. Visitor views course details: lessons, videos, quizzes, assignments, reviews.
4. If course is free: clicking checkout enrolls instantly (server-side enrollment logic).
5. If paid: checkout creates a Stripe Checkout Session; on success, server records `Payment` and creates `UserCourse` enrollment and sends confirmation email.
6. Enrolled users can watch videos (video access requires `lecture` query param and enrollment), take quizzes (records saved to `UserRecord`), and submit assignments (`Submission`).

## 🔎 Notes on Code-driven Features

- Quiz import: The `Quiz` model `save()` hook will call `parse_and_save_aiken()` when a `quiz_file` is uploaded — this parses Aiken-format files into `Question` and `Option` records.
- Video durations are computed by `Utils_File/video_durations.py` and displayed in course listings.
- Email sending uses Django SMTP settings loaded from `.env`.
- Stripe keys are present as placeholders in `settings.py` — add real keys in environment variables for payment.

## ❌ What This Project Does NOT Include (based on code)

- No explicit AI integrations (no calls to OpenAI/Azure/etc.) are present in the repository.
- No asynchronous/background task queue (Celery/RQ) is configured.
- No external Google Drive integration, PDF export, or code-runner subsystem is present in the codebase.

## 📈 SEO Keywords (suggested repository tags & keywords)

- Django LMS
- Online Course Platform
- E-learning Django
- Stripe Django Payments
- Quiz Engine Aiken
- Django Courses
- Open Source LMS
- Video Lessons Django
- Assignment Submission
- Email Authentication Django

## 🤝 Contribution

- Keep secrets out of Git — use `.env` for keys.
- Follow project style (Django templates + views + models). Add tests under `app/tests.py` before large refactors.

## Appendix — Useful Paths

- Code: `TechBuilt/` and `app/`
- Templates: `templates/`
- Static: `static/`, `staticfiles/`
- Utilities: `Utils_File/parse_and_save_aiken.py`, `Utils_File/video_durations.py`
- Requirements: `requirements.txt`

---

If you want, I can:
- Add this README into the repo (I will create `README.md`).
- Replace placeholder Stripe keys with environment-driven lookups in `settings.py` (suggested change, will not modify without permission).
- Run a static check of the repository and create a minimal `Procfile`/Dockerfile for deployment.

Would you like me to commit the README into the repository now? (I can add it as `README.md` under the project root.)