# src/apps/enrollments/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Enrollment
from .serializers import EnrollmentSerializer
from django_filters.rest_framework import DjangoFilterBackend

class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student_id', 'course_id', 'status']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Enrollment.objects.none()

        # Admins/Staff see all
        if user.is_staff:
            return Enrollment.objects.all()

        # Students see their own enrollments
        # Instructors might see enrollments for their courses (add logic if needed)
        return Enrollment.objects.filter(student=user)

    def perform_create(self, serializer):
        # Ensure the user creating the enrollment is the student enrolling
        # Or allow admins/staff to enroll others
        requesting_user = self.request.user
        student_id_payload = serializer.validated_data.get('student_id')

        if not requesting_user.is_staff and requesting_user.id != student_id_payload:
            raise PermissionDenied("You can only create enrollments for yourself.")

        # Prevent enrolling if student_id doesn't match current user (unless admin)
        serializer.save(student_id=student_id_payload) # Pass validated ID

    def get_permissions(self):
        """Allow students to create/read/delete their own, admins full access."""
        if self.action in ['create']:
            # Any authenticated user can attempt to create (validation handles specifics)
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
             # Allow owner or admin to modify/delete
            return [permissions.IsAuthenticated(), IsOwnerOrAdminEnrollment()]
        else: # list, retrieve
             # Any authenticated user can list/retrieve (queryset filters appropriately)
            return [permissions.IsAuthenticated()]

    # Override perform_destroy for soft delete
    def perform_destroy(self, instance):
        # Optional: Check permissions again before deletion
        if not self.request.user.is_staff and self.request.user != instance.student:
             raise PermissionDenied("You cannot delete this enrollment.")
        instance.soft_delete()


# Custom Permission Helper (Optional but good practice)
class IsOwnerOrAdminEnrollment(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an enrollment or admins to edit/delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_staff:
            return True
        # Otherwise, only the student who owns the enrollment
        return obj.student == request.user
