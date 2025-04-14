# src/apps/enrollments/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Enrollment
from apps.courses.models import Course
# Assuming serializers for related models are available
# Adjust imports based on your actual project structure
try:
    from apps.users.serializers import UserSerializer
except ImportError:
    # Define a minimal fallback UserSerializer if the import fails
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ('id', 'username', 'email') # Minimal fields

try:
    # Import a potentially simplified CourseSerializer for nesting
    # Avoid deep nesting if possible for performance
    class NestedCourseSerializer(serializers.ModelSerializer):
        # Maybe include instructor very simply here if needed
        instructor = serializers.StringRelatedField(read_only=True)
        class Meta:
            model = Course
            fields = ('id', 'title', 'instructor') # Only essential fields

    # Use the full serializer if detailed course info is needed
    from apps.courses.serializers import CourseSerializer
except ImportError:
    # Define minimal fallback CourseSerializers if imports fail
    class NestedCourseSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()

    class CourseSerializer(serializers.Serializer):
         id = serializers.IntegerField()
         title = serializers.CharField()
         description = serializers.CharField()
         price = serializers.DecimalField(max_digits=10, decimal_places=2)


User = get_user_model()

class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Enrollment model (MVP Focused).
    Handles viewing enrollments and creating new ones (enrolling).
    Unenrollment (delete) is handled by the ViewSet action.
    No updates needed for MVP.
    """

    # --- Read-only Nested Representations ---
    # Show basic student details when reading an enrollment
    student = UserSerializer(read_only=True)

    # Show basic course details when reading an enrollment
    # Use NestedCourseSerializer for potentially better performance in lists
    course = NestedCourseSerializer(read_only=True)
    # Alternatively, use the full CourseSerializer if more detail is needed:
    # course = CourseSerializer(read_only=True)

    # --- Write-only Fields for Creation ---
    # User needs to provide the ID of the course they want to enroll in.
    # Using PrimaryKeyRelatedField validates existence automatically.
    # source='course' links this input directly to the 'course' model field on write.
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), # Validates against non-deleted courses by default manager
        source='course',
        write_only=True,
        required=True, # Must provide course_id when enrolling
        help_text="ID of the course to enroll in."
    )

    # --- Read-only Computed Fields ---
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Enrollment
        # Fields to include in the API representation
        fields = [
            'id',               # Enrollment ID
            'student',          # Nested student details (read-only)
            'course',           # Nested course details (read-only)
            'course_id',        # Course ID (write-only, for create)
            'enrollment_date',  # Read-only timestamp
            'status',           # Current status (read-only for MVP)
            'status_display',   # Human-readable status (read-only)
            'created_at',       # Read-only timestamp
            'updated_at',       # Read-only timestamp
        ]

        # Fields that are never set directly via the API input (or derived)
        read_only_fields = (
            'id',
            'student',          # Set automatically by view based on request.user
            'course',           # The nested object is read-only via this field
            'enrollment_date',
            'status',           # Status is not updatable via this serializer in MVP
            'status_display',
            'created_at',
            'updated_at',
        )

        # Define extra constraints or options for specific fields
        extra_kwargs = {
            # 'status' is read-only based on above, model default applies on create
            'course_id': {'required': True}, # Explicitly require course_id on create
        }

    # --- Custom Validation ---
    def validate(self, data):
        """
        Perform cross-field validation for enrollment creation.
        """
        # Access the requesting user from the context passed by the view
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            # This check ensures we have a valid user context, crucial for validation logic.
            # In standard DRF views, this should always be present for authenticated requests.
            raise serializers.ValidationError("Authentication context is required for validation.")
        user = request.user

        # Retrieve the Course object from validated data (due to source='course')
        course_to_enroll = data.get('course')
        if not course_to_enroll:
            # This should be caught by 'required=True' on course_id, but double-check defense
            raise serializers.ValidationError({"course_id": "Course ID must be provided."})

        # --- MVP Validation Rules ---

        # 1. Prevent instructors from enrolling
        # Check if the user has a profile and if their role is instructor
        if hasattr(user, 'profile') and user.profile.role == Profile.Role.INSTRUCTOR:
            raise serializers.ValidationError("Instructors cannot enroll in courses.")

        # 2. Check if the user is already enrolled in this course (and not soft-deleted)
        # Uses the default manager ('objects') which excludes soft-deleted records
        if Enrollment.objects.filter(student=user, course=course_to_enroll).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")

        # 3. Optional but recommended: Check if the target course is actually active
        # if course_to_enroll.status != Course.Status.ACTIVE:
        #     raise serializers.ValidationError("You can only enroll in 'Active' courses.")

        # --- End Validation Rules ---

        return data # Return the validated data dictionary

    # --- Object Creation Logic ---
    def create(self, validated_data):
        """
        Handles the creation of a new Enrollment instance.
        The 'student' field is expected to be injected into validated_data
        by the view calling serializer.save(student=request.user).
        """
        # Ensure 'student' was correctly passed from the view context
        if 'student' not in validated_data:
            # This indicates an issue in the view logic where .save(student=...) wasn't called correctly.
            raise serializers.ValidationError(
                {"detail": "Internal error: Student information missing during enrollment creation."}
            )

        # 'course' object is already in validated_data thanks to source='course' on PrimaryKeyRelatedField
        # The default 'status' from the model ('active') will be used automatically.

        try:
            # Create the enrollment using all validated data (includes 'student' and 'course')
            enrollment = Enrollment.objects.create(**validated_data)
        except Exception as e:
            # Catch potential database constraint errors or other issues
            # Log the error e for debugging purposes
            print(f"Error creating enrollment: {e}")
            raise serializers.ValidationError(f"Failed to create enrollment. Please try again. Error: {e}")

        return enrollment

    # No update method needed for MVP, as enrollments are only created or deleted.
