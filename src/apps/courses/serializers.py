# src/apps/courses/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied

from .models import Course

try:
    # Using a simple serializer for nested display is often sufficient
    # and avoids potential circular imports if UserSerializer also nests CourseSerializer
    class SimpleUserSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ('id', 'username', 'first_name', 'last_name')

    # Keep the full UserSerializer import if you need more details nested
    from apps.users.serializers import UserSerializer
except ImportError:
    # Fallback or placeholder if UserSerializer is simple or defined differently
    class SimpleUserSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ('id', 'username') # Minimal fallback

    # Fallback for the main UserSerializer if needed elsewhere
    class UserSerializer(serializers.ModelSerializer):
         class Meta:
            model = get_user_model()
            fields = ("id", "username", "email", "first_name", "last_name", "is_staff")


User = get_user_model()


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model (MVP Focused).
    Handles conversion between Course instances and JSON for the API.
    Includes nested instructor details for reading.
    Accepts data for creation (instructor set by view) and update (admin can change instructor).
    Handles image uploads and removal.
    """

    # --- Read-only Computed/Related Fields ---
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    # Use the simpler nested serializer for read operations
    instructor = SimpleUserSerializer(read_only=True)

    # --- Write-only Fields ---
    # Accepts the instructor's ID during PUT/PATCH requests *by an Admin*.
    # PrimaryKeyRelatedField handles existence validation.
    # source='instructor' means this field will provide the 'instructor' User object
    # to validated_data upon successful validation of the ID.
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="instructor",
        write_only=True,
        required=False,  # Not required for create (set by view), optional for admin update
        allow_null=True,  # Allow admin to potentially unassign (if model allows null instructor)
        help_text="ID of the user to assign as instructor. Only changeable by Admin on update.",
    )

    image = serializers.ImageField(
        required=False,
        allow_null=True,
        use_url=True, # Ensure the URL is returned, not just the path
        help_text="Upload an image file for the course (optional). Send null to remove the existing image.",
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "price",
            "instructor",       # Read-only nested object
            "instructor_id",    # Write-only field for ID input
            "status",
            "status_display",
            "image",            # Read/Write field for image URL/Upload
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "instructor",       # The nested representation is read-only
            "status_display",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "title": {"required": True, "allow_blank": False},
            "description": {"required": True, "allow_blank": False},
            "price": {"required": True},
            "status": {"required": False}, # Defaults in model
            # instructor_id and image handled explicitly above
        }

    # --- Custom Validation Methods ---
    def validate_price(self, value):
        """Ensures the price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    # Note: No validate_instructor_id method needed here.
    # PrimaryKeyRelatedField handles the check if the user ID exists.
    # The permission check (is the updater an Admin?) is handled in the update method below.

    # --- Object Creation and Update Logic ---
    def create(self, validated_data):
        """
        Handles creation of a new Course instance.
        'instructor' must be passed via serializer.save(instructor=...) in the view.
        Handles optional image upload.
        """
        # Instructor should be injected by the view's perform_create
        if 'instructor' not in validated_data:
             # This check ensures the view logic passed the instructor correctly
             raise serializers.ValidationError({"detail": "Internal error: Instructor must be set during creation."})

        image_file = validated_data.pop("image", None)
        try:
            course = Course.objects.create(**validated_data)
        except TypeError as e:
             raise serializers.ValidationError(f"Failed to create course. Missing required data? Error: {e}")
        except DjangoValidationError as e:
             raise serializers.ValidationError(e.message_dict)

        if image_file:
            course.image = image_file
            course.save(update_fields=["image", "updated_at"])

        return course

    def update(self, instance, validated_data):
        """
        Handles updating an existing Course instance.
        Allows *Admin* to change the instructor via instructor_id (source='instructor').
        Handles image updates/removal.
        """
        requesting_user = self.context["request"].user

        # Check if 'instructor' (resolved from instructor_id) is in validated_data
        new_instructor_resolved = validated_data.pop('instructor', None)
        # Also check if 'instructor_id' was explicitly in the *incoming* payload
        instructor_id_in_payload = 'instructor_id' in self.initial_data

        if instructor_id_in_payload:
            # Instructor ID was provided in the request
            if not requesting_user.is_staff:
                 # Only Admins are allowed to attempt changing the instructor
                 raise PermissionDenied("Only Admins can change the course instructor.")

            # Admin is making the request, check the value they sent
            payload_instructor_id = self.initial_data['instructor_id']
            if payload_instructor_id is None:
                 # Admin explicitly wants to set instructor to null
                 if Course._meta.get_field("instructor").null:
                     instance.instructor = None
                 else:
                     raise serializers.ValidationError({"instructor_id": "Instructor cannot be set to null for this course."})
            elif new_instructor_resolved:
                 # Admin provided a valid ID, and it resolved to a user
                 instance.instructor = new_instructor_resolved
            else:
                 # Admin provided an ID, but it didn't resolve (PrimaryKeyRelatedField should have caught invalid ID)
                 # This case might not be reachable if PrimaryKeyRelatedField validation works correctly
                 raise serializers.ValidationError({"instructor_id": "Invalid instructor ID provided."})

        # Handle image update/removal
        image_update = validated_data.pop("image", Ellipsis)
        if image_update is not Ellipsis: # Check if 'image' key was present in request data
            instance.image = image_update # Assign the new file or None

        # Update remaining fields from validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.save() # Model's save handles updated_at
        except DjangoValidationError as e:
             raise serializers.ValidationError(e.message_dict)

        return instance
