"""
Development settings for TechBuilt Open School (TBOS).

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa: F401,F403

# ==============================
# DEBUG
# ==============================

DEBUG = True

# ==============================
# DATABASE
# ==============================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ==============================
# SECURITY (relaxed for local dev)
# ==============================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==============================
# STATIC FILES
# ==============================

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ==============================
# CACHE (local memory for dev)
# ==============================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ==============================
# EMAIL (console backend for dev)
# ==============================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================
# CORS (allow all in dev)
# ==============================

CORS_ALLOW_ALL_ORIGINS = True

# ==============================
# DRF RENDERERS (add browsable API in dev)
# ==============================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# ==============================
# LOGGING (more verbose in dev)
# ==============================

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
