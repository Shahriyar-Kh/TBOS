"""
Application-wide constants for TechBuilt Open School.
"""

# User roles
ROLE_ADMIN = "admin"
ROLE_INSTRUCTOR = "instructor"
ROLE_STUDENT = "student"

ALL_ROLES = (ROLE_ADMIN, ROLE_INSTRUCTOR, ROLE_STUDENT)
REGISTRATION_ROLES = (ROLE_STUDENT, ROLE_INSTRUCTOR)

# Course statuses
COURSE_DRAFT = "draft"
COURSE_PUBLISHED = "published"
COURSE_ARCHIVED = "archived"

# Payment statuses
PAYMENT_PENDING = "pending"
PAYMENT_COMPLETED = "completed"
PAYMENT_FAILED = "failed"
PAYMENT_REFUNDED = "refunded"

# Notification types
NOTIFICATION_ENROLLMENT = "enrollment"
NOTIFICATION_PAYMENT = "payment"
NOTIFICATION_ASSIGNMENT = "assignment"
NOTIFICATION_QUIZ = "quiz"
NOTIFICATION_GRADE = "grade"
NOTIFICATION_CERTIFICATE = "certificate"
NOTIFICATION_ANNOUNCEMENT = "announcement"
NOTIFICATION_SYSTEM = "system"

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
