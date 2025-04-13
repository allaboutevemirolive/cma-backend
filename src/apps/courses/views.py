# src/apps/courses/views.py

from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course
from .serializers import CourseSerializer
from .permissions import IsAdminOrInstructor


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows courses to be viewed, created, updated, or deleted.

    **Permissions:**
    - List/Retrieve (GET): Any authenticated user.
    - Create/Update/Partial Update/Destroy: Admin users or users with the 'Instructor' role only.
    - Restore/Deleted List: Admin users or users with the 'Instructor' role only.

    **Filtering:**
    Supports filtering by `status` and `instructor_id`.

    **Searching:**
    Supports searching across `title`, `description`, and `instructor__username`.

    **Ordering:**
    Supports ordering by `title`, `price`, `created_at`, `status`, `instructor__username`.

    **Deletion:**
    Uses soft delete. Deleted items are hidden by default.
    """

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
        """
        Returns queryset for non-deleted courses only.
        """
        return Course.objects.all()

    def get_permissions(self):
        """
        Returns permission classes depending on the action.
        """
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "restore",
            "deleted_list",
        ]:
            permission_classes = [IsAdminOrInstructor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        """
        Soft delete the course instead of hard delete.
        """
        instance.soft_delete()

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrInstructor],
        url_path="restore",
    )
    def restore(self, request, pk=None):
        """
        Restore a soft-deleted course.
        """
        try:
            course = Course.all_objects.get(pk=pk, is_deleted=True)
            course.restore()
            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Soft-deleted course not found or already restored."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAdminOrInstructor],
        url_path="deleted",
    )
    def deleted_list(self, request):
        """
        List all soft-deleted courses.
        """
        deleted_courses = Course.all_objects.filter(is_deleted=True)
        page = self.paginate_queryset(deleted_courses)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deleted_courses, many=True)
        return Response(serializer.data)
