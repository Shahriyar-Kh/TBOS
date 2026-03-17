from django.core.cache import cache


DASHBOARD_CACHE_TTL_SECONDS = 300


def student_dashboard_key(user_id):
    return f"analytics:student:{user_id}:dashboard"


def instructor_dashboard_key(user_id):
    return f"analytics:instructor:{user_id}:dashboard"


def admin_dashboard_key(start_date=None, end_date=None):
    start = start_date or "all"
    end = end_date or "all"
    return f"analytics:admin:dashboard:{start}:{end}"


def get_dashboard_cache(key):
    return cache.get(key)


def set_dashboard_cache(key, value):
    cache.set(key, value, DASHBOARD_CACHE_TTL_SECONDS)


def invalidate_student_dashboard(user_id):
    cache.delete(student_dashboard_key(user_id))


def invalidate_instructor_dashboard(user_id):
    cache.delete(instructor_dashboard_key(user_id))


def invalidate_admin_dashboard():
    cache.delete(admin_dashboard_key())
