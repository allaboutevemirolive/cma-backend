# backend/courses/views.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course
from .serializers import CourseSerializer
# from rest_framework.permissions import IsAuthenticated # For Bonus: JWT Auth

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows courses to be viewed or edited.

    Supports filtering by `status` and `instructor_id`.
    Example: `/api/courses/?status=active&instructor_id=1`

    Uses soft delete for DELETE requests.
    """
    queryset = Course.objects.all() # Uses the default manager (excludes soft-deleted)
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter] # Add Ordering and Search
    filterset_fields = ['status', 'instructor_id'] # Fields available for filtering
    search_fields = ['title', 'description']       # Fields available for searching (?search=...)
    ordering_fields = ['title', 'price', 'created_at', 'status'] # Fields available for ordering (?ordering=price)

    # Optional: Add Permissions for Bonus Features
    # permission_classes = [IsAuthenticated] # Example: Requires users to be logged in

    # Override perform_destroy for soft delete (though model's delete handles it)
    # This override ensures we return 204 No Content as expected by REST standards
    # The model's delete() method already does the soft delete logic.
    def perform_destroy(self, instance):
        instance.soft_delete() # Call our custom soft delete method

    # Optional: Add an action to view deleted items (e.g., for admins)
    # @action(detail=False, methods=['get'], url_path='deleted')
    # def deleted_courses(self, request):
    #     deleted_courses = Course.all_objects.deleted_objects() # Use the manager that includes all
    #     page = self.paginate_queryset(deleted_courses)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(deleted_courses, many=True)
    #     return Response(serializer.data)

    # Optional: Add an action to restore a deleted item
    # @action(detail=True, methods=['post'])
    # def restore(self, request, pk=None):
    #     try:
    #         course = Course.all_objects.get(pk=pk, is_deleted=True) # Find only among deleted
    #         course.restore()
    #         serializer = self.get_serializer(course)
    #         return Response(serializer.data)
    #     except Course.DoesNotExist:
    #         return Response({'error': 'Deleted course not found.'}, status=status.HTTP_404_NOT_FOUND)
