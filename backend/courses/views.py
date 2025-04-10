# backend/courses/views.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action # Optional: for custom actions like restore
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course
from .serializers import CourseSerializer
from .permissions import IsAdminOrInstructor # Custom permission for RBAC

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows courses to be viewed, created, updated, or deleted.

    **Permissions:**
    *   List/Retrieve (GET): Any authenticated user.
    *   Create/Update/Delete (POST, PUT, PATCH, DELETE): Admin users or users in the 'Instructors' group only.

    **Filtering:**
    Supports filtering by `status` and `instructor_id`.
    Example: `/api/courses/?status=active&instructor_id=1`

    **Searching:**
    Supports searching across `title` and `description` fields.
    Example: `/api/courses/?search=python`

    **Ordering:**
    Supports ordering by `title`, `price`, `created_at`, `status`.
    Example: `/api/courses/?ordering=-price` (descending price)

    **Deletion:**
    Uses soft delete for DELETE requests. Deleted items are hidden by default.
    """
    # queryset = Course.objects.all() # Use get_queryset() for potential future user-based filtering
    serializer_class = CourseSerializer

    # --- Filtering, Searching, Ordering ---
    filter_backends = [
        DjangoFilterBackend,        # For field-based filtering
        filters.SearchFilter,       # For ?search= parameter
        filters.OrderingFilter      # For ?ordering= parameter
    ]
    filterset_fields = ['status', 'instructor_id'] # Fields available for precise filtering
    search_fields = ['title', 'description']       # Fields searched via ?search=
    ordering_fields = ['title', 'price', 'created_at', 'status'] # Fields allowed for ordering

    # --- Permissions ---
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires,
        based on the action being performed.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'restore', 'deleted_courses']:
             # Write actions require Admin or Instructor role
             # Default IsAuthenticated is already checked by global settings
            permission_classes = [IsAdminOrInstructor]
        else:
             # Read actions (list, retrieve) only require authentication (handled globally)
            permission_classes = [IsAuthenticated] # Explicitly state, though global setting covers this

        # Note: We rely on the global DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]
        # to ensure the user is logged in *before* these more specific checks run.
        # If the global default wasn't set, we'd need [IsAuthenticated, IsAdminOrInstructor]
        # for the write actions.
        return [permission() for permission in permission_classes]

    # --- Queryset ---
    def get_queryset(self):
        """
        Returns the queryset that should be used for list views.
        Defaults to the Course model's default manager (non-deleted items).
        Could be overridden later to filter based on the user (e.g., show only courses taught by instructor).
        """
        # Ensure only non-deleted items are shown by default list/detail views
        return Course.objects.all() # Uses the default manager which excludes is_deleted=True

    # --- Soft Delete ---
    def perform_destroy(self, instance):
        """
        Overrides the default destroy action to perform a soft delete.
        The actual logic is in the model's delete() method. This ensures
        the instance's `soft_delete()` method is called.
        """
        instance.soft_delete() # Calls the model method which sets flags and saves

    # --- Optional: Custom Actions for Soft Delete Management ---

    # @action(detail=True, methods=['post'], permission_classes=[IsAdminOrInstructor]) # Ensure correct permissions
    # def restore(self, request, pk=None):
    #     """
    #     Restores a soft-deleted course instance. Requires Admin/Instructor role.
    #     """
    #     try:
    #         # Use all_objects manager to find the instance even if deleted
    #         course = Course.all_objects.get(pk=pk, is_deleted=True)
    #         course.restore()
    #         serializer = self.get_serializer(course)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except Course.DoesNotExist:
    #         return Response({'error': 'Soft-deleted course not found.'}, status=status.HTTP_404_NOT_FOUND)

    # @action(detail=False, methods=['get'], url_path='deleted', permission_classes=[IsAdminOrInstructor]) # Ensure correct permissions
    # def deleted_courses(self, request):
    #     """
    #     Lists only the soft-deleted courses. Requires Admin/Instructor role.
    #     """
    #     deleted_courses = Course.all_objects.deleted_objects() # Use the specific manager method

    #     # Apply pagination from settings
    #     page = self.paginate_queryset(deleted_courses)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(deleted_courses, many=True)
    #     return Response(serializer.data)
