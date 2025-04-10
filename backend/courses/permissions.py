# backend/courses/permissions.py

from rest_framework import permissions

class IsAdminOrInstructor(permissions.BasePermission):
    """
    Allows access only to admin users or users in the 'Instructors' group.
    """
    message = "You do not have permission to perform this action." # Custom message

    def has_permission(self, request, view):
        # Check if user is authenticated first (should be handled by IsAuthenticated already)
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow if user is staff (admin)
        if request.user.is_staff:
            return True

        # Allow if user is in the 'Instructors' group
        # Using exists() is efficient
        return request.user.groups.filter(name='Instructors').exists()

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to any authenticated user, but only admin users for write operations.
    Useful if only admins should modify certain things. Not used in the current CourseViewSet logic, but good example.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS: # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_staff
