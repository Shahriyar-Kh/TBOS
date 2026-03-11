from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsInstructor(BasePermission):
    """Allow access only to instructor users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "instructor"
        )


class IsStudent(BasePermission):
    """Allow access only to student users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsAdminOrInstructor(BasePermission):
    """Allow access to admin or instructor users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "instructor")
        )


class IsOwner(BasePermission):
    """Object-level permission allowing only the resource owner."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "student"):
            return obj.student == request.user
        if hasattr(obj, "instructor"):
            return obj.instructor == request.user
        return False


class IsOwnerOrAdmin(BasePermission):
    """Object-level: allow owner or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return IsOwner().has_object_permission(request, view, obj)


class IsOwnerInstructor(BasePermission):
    """
    View-level: user must be an instructor.
    Object-level: instructor must own the course (obj.instructor == user).
    Admins bypass the ownership check.
    Supports multi-level traversal: obj.course, obj.section.course, etc.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "instructor")
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        # Traverse to the owning course
        if hasattr(obj, "section"):
            # Lesson → section → course
            course = getattr(obj.section, "course", None)
        else:
            course = getattr(obj, "course", obj)
        instructor = getattr(course, "instructor", None)
        return instructor == request.user


class IsEnrolledOrInstructor(BasePermission):
    """Allow enrolled students or the course instructor."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == "admin":
            return True
        course = getattr(obj, "course", obj)
        if user.role == "instructor" and course.instructor == user:
            return True
        if user.role == "student":
            return course.enrollments.filter(student=user, is_active=True).exists()
        return False
