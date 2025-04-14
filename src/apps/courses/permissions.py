# src/apps/courses/permissions.py
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admin users (is_staff)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsInstructorUser(permissions.BasePermission):
    """Allows access only to users with the 'instructor' role."""

    def has_permission(self, request, view):
        # Check profile exists and role is instructor
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == "instructor"
        )


class IsCourseOwnerInstructor(permissions.BasePermission):
    """
    Object-level permission to only allow the course's instructor to modify it.
    """

    def has_object_permission(self, request, view, obj):
        # Assumes obj is a Course instance
        return obj.instructor == request.user


class IsCourseOwnerInstructorOrAdmin(permissions.BasePermission):
    """
    Object-level permission allowing the course's instructor OR an admin.
    """

    def has_object_permission(self, request, view, obj):
        # Assumes obj is a Course instance
        return obj.instructor == request.user or request.user.is_staff


# Note: You might combine these or use DRF's composition (e.g., IsAdminUser | IsInstructorUser)
# but explicit classes can be clearer.
