# src/apps/enrollments/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Enrollment
from .serializers import EnrollmentSerializer
from .permissions import IsEnrollmentOwnerOrAdmin  # <-- Import custom permission
from django_filters.rest_framework import DjangoFilterBackend


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["student_id", "course_id", "status"]  # Keep filtering

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Enrollment.objects.none()

        # Admins see all non-deleted enrollments
        if user.is_staff:
            return Enrollment.objects.all()

        # Instructors - MVP doesn't require them to see enrollments easily, focus on student view
        # if hasattr(user, 'profile') and user.profile.role == 'instructor':
        # return Enrollment.objects.filter(course__instructor=user) # Example if needed later

        # Regular Users see their own non-deleted enrollments
        return Enrollment.objects.filter(student=user)

    def get_permissions(self):
        """Set permissions based on action for MVP."""
        if self.action == "create":
            # Any authenticated user can attempt to enroll (view logic restricts student)
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["list", "retrieve"]:
            # Authenticated users can list/retrieve (queryset filters for them)
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == "destroy":
            # Only the owner (student) or admin can unenroll (delete)
            permission_classes = [IsEnrollmentOwnerOrAdmin]
        elif self.action in ["update", "partial_update"]:
            # Not needed for MVP - disable
            permission_classes = [permissions.IsAdminUser]  # Or just DenyAll
        else:
            permission_classes = [permissions.IsAuthenticated]  # Default
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Enroll the currently logged-in user."""
        user = self.request.user
        course_id = serializer.validated_data.get("course_id")

        # Prevent instructors from enrolling
        if hasattr(user, "profile") and user.profile.role == "instructor":
            raise PermissionDenied("Instructors cannot enroll in courses.")

        # Check if already enrolled (using serializer validation is better)
        if Enrollment.objects.filter(student=user, course_id=course_id).exists():
            raise ValidationError("You are already enrolled in this course.")

        # Save with the current user as the student
        serializer.save(student=user)  # Pass student object directly

    def perform_destroy(self, instance):
        """Perform soft delete (unenroll). Permission check done by IsEnrollmentOwnerOrAdmin."""
        # Permission check already done by get_permissions + IsEnrollmentOwnerOrAdmin
        instance.soft_delete()

    # Disable update methods explicitly for MVP
    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'PUT' not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method 'PATCH' not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
