# src/apps/enrollments/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Enrollment
from apps.courses.models import Course
# Need Profile model to check roles during validation
from apps.profiles.models import Profile # Corrected: Import Profile

# Assuming serializers for related models are available
# Adjust imports based on your actual project structure
try:
    # Import a UserSerializer (potentially simplified)
    from apps.users.serializers import UserSerializer
except ImportError:
    # Define a minimal fallback UserSerializer if the import fails
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ('id', 'username', 'email') # Minimal fields

try:
    # Import a potentially simplified CourseSerializer for nesting
    class NestedCourseSerializer(serializers.ModelSerializer):
        # Maybe include instructor very simply here if needed
        instructor = serializers.StringRelatedField(read_only=True) # Show instructor username
        class Meta:
            model = Course
            fields = ('id', 'title', 'instructor') # Only essential fields for context

    # Use the full serializer if detailed course info is needed (less common for enrollment lists)
    # from apps.courses.serializers import CourseSerializer
except ImportError:
    # Define minimal fallback CourseSerializers if imports fail
    class NestedCourseSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        instructor = serializers.CharField() # Placeholder

    # class CourseSerializer(serializers.Serializer): # Full fallback if needed elsewhere
    #      id = serializers.IntegerField()
    #      title = serializers.CharField()
    #      description = serializers.CharField()
    #      price = serializers.DecimalField(max_digits=10, decimal_places=2)


User = get_user_model()

class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Enrollment model (MVP Focused).
    Handles viewing enrollments and creating new ones (enrolling).
    Unenrollment (delete) is handled by the ViewSet action.
    Updates are disabled for MVP.
    """

    # --- Read-only Nested Representations ---
    student = UserSerializer(read_only=True)
    course = NestedCourseSerializer(read_only=True)

    # --- Write-only Fields for Creation ---
    # Uses PrimaryKeyRelatedField for validation and links source='course'
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), # Validates against non-deleted courses
        source='course',
        write_only=True,
        required=True,
        help_text="ID of the course to enroll in."
    )

    # --- Read-only Computed Fields ---
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student',          # Read-only nested object
            'course',           # Read-only nested object
            'course_id',        # Write-only input field
            'enrollment_date',
            'status',           # Read-only status (default set by model)
            'status_display',
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'id',
            'student',          # Set by view
            'course',           # Read representation of the nested object
            'enrollment_date',
            'status',           # Not directly updatable via this serializer
            'status_display',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'course_id': {'required': True}, # Ensure course_id is always provided on POST
        }

    # --- Custom Validation ---
    def validate(self, data):
        """
        Perform cross-field validation for enrollment creation.
        Ensures only students can enroll and prevents duplicate enrollments.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            # This check is defensive; DRF views should provide this context.
            raise serializers.ValidationError("Authentication context is required.")
        user = request.user

        # The course object is already validated and present in 'data' due to source='course'
        course_to_enroll = data.get('course')
        # The 'course_id' field itself ensures the course exists. If not, PrimaryKeyRelatedField raises error.
        if not course_to_enroll:
             # This case might be hit if queryset is empty or field is optional (not the case here)
             raise serializers.ValidationError({"course_id": "Valid Course ID must be provided."})


        # --- CORRECTED MVP Validation Rules ---
        # 1. Allow ONLY students to enroll.
        #    Check if the user has a profile and if their role is NOT student.
        user_role = None
        if hasattr(user, 'profile'):
            user_role = user.profile.role
        else:
            # If profile somehow doesn't exist, they definitely can't be a student yet
             raise serializers.ValidationError("User profile not found. Cannot determine role.")

        if user_role != Profile.Role.STUDENT:
             # Raise error if user is Instructor, Admin, or any other non-student role
             raise serializers.ValidationError(f"Users with role '{user_role}' cannot enroll in courses.")


        # 2. Check if already enrolled (active enrollment)
        if Enrollment.objects.filter(student=user, course=course_to_enroll).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")

        # Optional: Check if course is active (if you want this restriction)
        # if course_to_enroll.status != Course.Status.ACTIVE:
        #     raise serializers.ValidationError("Enrollment is only allowed in 'Active' courses.")

        return data

    # --- Object Creation Logic ---
    def create(self, validated_data):
        """
        Handles the creation of a new Enrollment instance.
        Assumes the 'student' object is passed in via serializer.save(student=...)
        by the view.
        """
        # Ensure 'student' was correctly passed from the view context
        if 'student' not in validated_data:
            # Indicates an issue in view logic
            # Log this internally if possible
            print("CRITICAL: Student object missing in validated_data during enrollment creation.")
            raise serializers.ValidationError({"detail": "Internal server error: Could not process enrollment."})

        # 'course' object is already in validated_data due to source='course'
        # Default 'status' ('active') is handled by the model definition

        try:
            enrollment = Enrollment.objects.create(**validated_data)
        except Exception as e:
            # Log the error for debugging
            # logger.error(f"Error creating enrollment for user {validated_data.get('student')} in course {validated_data.get('course')}: {e}")
            print(f"Error creating enrollment: {e}") # Simple print for now
            raise serializers.ValidationError(f"Could not complete enrollment. Error: {e}")

        return enrollment

    # --- Update Logic (Not needed for MVP) ---
    # def update(self, instance, validated_data):
    #     # MVP does not require updating enrollments via API
    #     raise NotImplementedError("Enrollment updates are not supported in this version.")
