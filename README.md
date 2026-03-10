# TBOS Backend

TBOS is a modular Django REST Framework backend for a learning management system. The legacy server-rendered monolith has been removed in favor of independent domain apps under apps and a single config package for deployment.

## Architecture

- config: settings, routing, ASGI/WSGI, Celery bootstrap
- apps: domain modules such as accounts, courses, quiz, assignments, payments, and notifications
- media: uploaded or synchronized media assets
- logs: runtime log files

Each domain app follows the same structure: models, serializers, views, urls, migrations, and services for business logic.

## Platform Stack

- Django 5.1
- Django REST Framework
- JWT authentication via Simple JWT
- OpenAPI schema and Swagger UI via drf-spectacular
- PostgreSQL-ready database configuration
- Redis cache and Celery broker/result backend
- Cloudinary-backed media storage
- Stripe payments

## API Surface

- Base API: /api/v1/
- Schema: /api/schema/
- Swagger UI: /api/docs/
- ReDoc: /api/redoc/

## Local Setup

1. Create a virtual environment and install requirements.
2. Copy .env.example to .env and fill in the required values.
3. Run migrations.
4. Start Django and Celery workers.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
celery -A config worker -l info
```

## Environment

The project supports either DATABASE_URL or discrete PostgreSQL variables. Redis and Cloudinary are configured via environment variables, and local development can still fall back to SQLite when PostgreSQL is not configured.

## Notes

- The backend is API-only. React or another SPA should consume the /api/v1/ endpoints.
- Django templates are retained only at the framework level where required by Swagger UI; no project templates are used.
- Business logic should live in app-level service modules, not in views.
