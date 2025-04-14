# src/apps/courses/views.py
from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

# Import specific permissions
from .permissions import (
    IsAdminUser,
    IsInstructorUser,
    IsCourseOwnerInstructor,
    IsCourseOwnerInstructorOrAdmin,
)
from .models import Course
from .serializers import CourseSerializer
from django_filters.rest_framework import DjangoFilterBackend


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "instructor_id"]
    search_fields = ["title", "description", "instructor__username"]
    ordering_fields = ["title", "price", "created_at", "status", "instructor__username"]

    def get_queryset(self):
        # Default manager ('objects') already excludes soft-deleted
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                # Admin sees all non-deleted courses
                return Course.objects.all()
            elif hasattr(user, "profile") and user.profile.role == "instructor":
                # Instructor sees all non-deleted courses for browsing/potentially managing theirs
                # Can refine later if instructors should only see their own in lists too
                return Course.objects.all()
            else:
                # Regular users see all non-deleted courses
                return Course.objects.all()
        return Course.objects.none()  # No courses for unauthenticated users

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Any authenticated user can list/retrieve courses
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == "create":
            # Only instructors can create
            permission_classes = [IsInstructorUser]
        elif self.action in ["update", "partial_update"]:
            # Only the course owner (instructor) or admin can update
            permission_classes = [IsCourseOwnerInstructorOrAdmin]
        elif self.action == "destroy":
            # Only the course owner (instructor) or admin can delete
            permission_classes = [IsCourseOwnerInstructorOrAdmin]
        elif self.action in ["restore", "deleted_list"]:
            # Only Admins can restore or list deleted (Adjust if Instructors should manage deleted own courses)
            permission_classes = [IsAdminUser]  # Changed as per strict MVP
        else:
            # Default deny? Or IsAuthenticated? Let's require auth by default.
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Set the instructor to the current user when creating."""
        if not (
            hasattr(self.request.user, "profile")
            and self.request.user.profile.role == "instructor"
        ):
            # This check is redundant if IsInstructorUser permission works, but good practice
            raise PermissionDenied(
                "Only users with the 'instructor' role can create courses."
            )
        # Pass instructor directly from the request user
        serializer.save(instructor=self.request.user)

    # perform_destroy uses soft delete from model (good)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUser],  # Only Admin can restore ANY course
        url_path="restore",
    )
    def restore(self, request, pk=None):
        """Restore a soft-deleted course (Admin only)."""
        try:
            # Use all_objects manager to find deleted items
            course = Course.all_objects.get(pk=pk, is_deleted=True)
            # Permission check already done by permission_classes
            course.restore()
            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Soft-deleted course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAdminUser],  # Only Admin can list deleted courses
        url_path="deleted",
    )
    def deleted_list(self, request):
        """List all soft-deleted courses (Admin only)."""
        deleted_courses = Course.all_objects.filter(is_deleted=True)
        page = self.paginate_queryset(deleted_courses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(deleted_courses, many=True)
        return Response(serializer.data)
