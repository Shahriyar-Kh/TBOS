"""
Test settings for TechBuilt Open School (TBOS).

Used automatically by pytest via pytest.ini:
    DJANGO_SETTINGS_MODULE = config.settings.test

Key differences from development:
- SECRET_KEY is set before base.py is imported so the test suite runs
  without a .env file (e.g. on CI or a fresh clone).
- In-memory SQLite database for fast, isolated test runs.
- Fastest password hasher to speed up tests.
- Disabled throttling so tests are not rate-limited.
- Django's dummy email backend.
"""

import os

# ------------------------------------------------------------------ #
# Must be set BEFORE importing base (base.py raises if not present)  #
# ------------------------------------------------------------------ #
os.environ.setdefault(
    "SECRET_KEY",
    "django-insecure-test-key-do-not-use-in-production",
)

from .development import *  # noqa: F401,F403

# ==============================
# DATABASE — fast in-memory SQLite
# ==============================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# ==============================
# PASSWORD HASHING — fastest for tests
# WARNING: MD5PasswordHasher is cryptographically weak.
# This MUST NEVER be used in development.py, production.py, or any
# settings file other than test.py.
# ==============================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ==============================
# EMAIL — store in memory (accessible via django.core.mail.outbox)
# ==============================

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ==============================
# THROTTLING — disable for tests
# ==============================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405

# ==============================
# CACHE — local memory (no Redis needed)
# ==============================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ==============================
# CELERY — run tasks synchronously
# ==============================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
