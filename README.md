# TechBuilt Open School (TBOS)

A production-ready, scalable LMS (Learning Management System) backend built with Django REST Framework. Monorepo with a React/Next.js frontend.

---

## Architecture

```
TBOS/
├── .env                        # Environment variables (root level)
├── .env.example                # Template for env vars
├── .gitignore                  # Single root gitignore
├── requirements.txt            # Python dependencies
├── README.md
│
├── TBOS_Backend/
│   ├── manage.py
│   ├── Procfile
│   ├── pytest.ini
│   │
│   ├── config/                 # Django project configuration
│   │   ├── settings/
│   │   │   ├── base.py         # Shared settings
│   │   │   ├── development.py  # Local dev overrides
│   │   │   └── production.py   # Production settings
│   │   ├── urls.py
│   │   ├── api_router.py
│   │   ├── celery.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── apps/                   # Django applications
│   │   ├── core/               # Shared utilities, permissions, pagination
│   │   ├── accounts/           # Auth, users, profiles
│   │   ├── courses/            # Course management
│   │   ├── lessons/            # Lesson content
│   │   ├── videos/             # Video content (YouTube, Cloudinary, S3)
│   │   ├── quiz/               # Quizzes & assessments
│   │   ├── assignments/        # Assignments & submissions
│   │   ├── enrollments/        # Student enrollments & progress
│   │   ├── payments/           # Stripe payments
│   │   ├── reviews/            # Course reviews & ratings
│   │   ├── analytics/          # Platform analytics
│   │   ├── ai_tools/           # AI quiz generation & suggestions
│   │   ├── certificates/       # Completion certificates
│   │   └── notifications/      # User notifications
│   │
│   ├── scripts/                # Operational scripts
│   │   ├── seed_database.py
│   │   ├── create_admin.py
│   │   ├── import_courses.py
│   │   └── data.json
│   │
│   ├── tests/                  # Test suite
│   │   ├── conftest.py
│   │   ├── accounts/
│   │   ├── courses/
│   │   └── ...
│   │
│   ├── media/                  # Uploaded media files
│   │   ├── avatars/
│   │   ├── courses/
│   │   ├── lessons/
│   │   ├── assignments/
│   │   ├── submissions/
│   │   ├── thumbnails/
│   │   └── quiz_files/
│   │
│   └── logs/                   # Runtime log files
│       ├── app.log
│       ├── error.log
│       └── requests.log
│
└── TBOS_Frontend/              # React / Next.js frontend
```

## App Architecture

Each app follows a clean three-layer architecture:

```
Views    → HTTP request/response layer
Services → Business logic layer
Models   → Database layer
```

## Platform Stack

| Component        | Technology                          |
|-----------------|--------------------------------------|
| Framework       | Django 5.1 + Django REST Framework   |
| Authentication  | JWT via Simple JWT                   |
| API Docs        | drf-spectacular (Swagger / ReDoc)    |
| Database        | PostgreSQL (SQLite for dev)          |
| Cache           | Redis                                |
| Task Queue      | Celery + Redis                       |
| Media Storage   | Cloudinary / AWS S3                  |
| Payments        | Stripe                               |
| Rate Limiting   | django-ratelimit + DRF throttling    |
| Testing         | pytest + pytest-django               |

## API Surface

| Endpoint          | Description                 |
|------------------|-----------------------------|
| `/api/v1/`       | API root with endpoint list |
| `/api/schema/`   | OpenAPI 3.0 schema          |
| `/api/docs/`     | Swagger UI                  |
| `/api/redoc/`    | ReDoc documentation         |

## Settings

Settings are split into three files under `config/settings/`:

- **base.py** — shared, environment-agnostic settings
- **development.py** — local dev (SQLite, console email, debug mode)
- **production.py** — production (PostgreSQL, Cloudinary, SSL, HSTS)

Set the active environment via:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.development  # local
export DJANGO_SETTINGS_MODULE=config.settings.production    # production
```

## Local Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run migrations & start server
cd TBOS_Backend
python manage.py migrate
python manage.py runserver

# 5. Start Celery worker (optional)
celery -A config worker -l info
```

## Scripts

```bash
cd TBOS_Backend
python scripts/create_admin.py         # Create admin user
python scripts/seed_database.py        # Seed categories, levels, languages
python scripts/import_courses.py       # Import courses from JSON
```

## Testing

```bash
cd TBOS_Backend
pytest
```

## API Response Format

All API responses follow a standard envelope:

```json
{
  "success": true,
  "message": "Operation completed.",
  "data": {}
}
```

Error responses:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {"field": ["Error detail"]},
  "status_code": 400
}
```
