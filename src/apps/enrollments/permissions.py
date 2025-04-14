# src/apps/enrollments/permissions.py
from rest_framework import permissions


class IsEnrollmentOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to the student who owns the enrollment or an admin.
    """

    def has_permission(self, request, view):
        # Basic check for authentication
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.is_staff:
            return True
        # Check if the request user is the student associated with the enrollment
        # Assumes obj is an Enrollment instance
        return obj.student == request.user
