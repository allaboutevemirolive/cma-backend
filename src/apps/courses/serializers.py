# src/apps/courses/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model  # Best practice to get the User model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied

from .models import Course

# Assuming UserSerializer is correctly placed and defined
# Adjust the import path if your UserSerializer is elsewhere
# Ensure the users app and its serializers are correctly structured
try:
    from apps.users.serializers import UserSerializer
except ImportError:
    # Fallback or placeholder if UserSerializer is simple or defined differently
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ("id", "username", "email", "first_name", "last_name", "is_staff")


User = get_user_model()  # Get the active User model


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model (MVP Focused).
    Handles conversion between Course instances and JSON for the API.
    Includes nested instructor details for reading.
    Accepts data for creation (instructor set by view) and update (admin can change instructor).
    Handles image uploads and removal.
    """

    # --- Read-only Computed/Related Fields ---
    # Provides a human-readable version of the status field.
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Nested representation of the instructor for read operations.
    instructor = UserSerializer(read_only=True)

    # --- Write-only Fields ---
    # Accepts the instructor's ID during PUT/PATCH requests *by an Admin*.
    # For CREATE, the instructor is set automatically from the request user in the view.
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),  # Queryset for validation if provided
        source="instructor",  # Link directly to the instructor field on write
        write_only=True,
        required=False,  # Not required for create (set by view), optional for update (admin only)
        allow_null=True,  # Allow admin to potentially unassign (if model allows null instructor)
        help_text="ID of the user to assign as instructor. Only changeable by Admin on update.",
    )

    # The 'image' field using ImageField handles both URL generation on read
    # and file upload handling (multipart/form-data) on write.
    # Setting allow_null=True allows sending 'null' to remove the image on update.
    image = serializers.ImageField(
        required=False,  # Image is not mandatory
        allow_null=True,  # Allow null input for clearing the image
        help_text="Upload an image file for the course (optional). Send null to remove the existing image.",
    )

    class Meta:
        model = Course
        # Define the fields to include in the API representation.
        fields = [
            "id",  # Primary key
            "title",  # Course title
            "description",  # Course description
            "price",  # Course price
            "instructor",  # Nested instructor details (read-only)
            "instructor_id",  # Instructor ID (write-only, for Admin updates)
            "status",  # Course status ('active'/'inactive'/'draft')
            "status_display",  # Read-only display version of status
            "image",  # Image field (handles upload/URL/removal)
            "created_at",  # Timestamp
            "updated_at",  # Timestamp
            # Excluded: 'is_deleted', 'deleted_at' (handled by viewsets/managers)
        ]

        # Fields that should not be set directly via the API input on read operations.
        read_only_fields = (
            "id",
            "instructor",  # The nested object is read-only via this field
            "status_display",
            "created_at",
            "updated_at",
        )

        # Define extra constraints or options for specific fields.
        extra_kwargs = {
            "title": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Course title is required.",
                    "blank": "Course title cannot be blank.",
                },
            },
            "description": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Course description is required.",
                    "blank": "Course description cannot be blank.",
                },
            },
            "price": {
                "required": True,
                "error_messages": {
                    "required": "Course price is required.",
                    "invalid": "Enter a valid price.",
                },
            },
            "status": {
                "required": False,  # Defaults to 'draft' in the model
            },
            # 'instructor_id' defined explicitly above
            # 'image' defined explicitly above
        }

    # --- Custom Validation Methods ---

    def validate_price(self, value):
        """Ensures the price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    # Optional: Add validation for instructor_id *if* provided, mainly for Admins
    def validate_instructor_id(self, value):
        """
        Checks if the provided instructor_id corresponds to a valid user,
        especially when an Admin is attempting to set/change the instructor.
        Basic existence check - role check can happen in view or permission.
        """
        if value is None:  # Handle explicit null assignment if allowed
            if (
                not self.instance
            ):  # Cannot assign null on create if model requires instructor
                # Check if model field allows null
                if not Course._meta.get_field("instructor").null:
                    raise serializers.ValidationError("Instructor cannot be null.")
            return None  # Allow null if model field allows it on update

        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"No user found with ID {value}.")

        # More specific role validation can be added here or handled by permissions/view logic
        # user = User.objects.get(pk=value)
        # if not (hasattr(user, 'profile') and user.profile.role == 'instructor') and not user.is_staff:
        #     raise serializers.ValidationError("Assigned user must have instructor role or be admin.")

        return value  # Return the validated user instance (due to source='instructor') or just the ID if not using source

    # --- Object Creation and Update Logic ---

    def create(self, validated_data):
        """
        Handles creation of a new Course instance.
        The 'instructor' is set in the view's perform_create method using request.user.
        Handles optional image upload.
        """
        # 'instructor' or 'instructor_id' should NOT be in validated_data if view sets it
        # validated_data.pop('instructor_id', None) # Remove if it somehow gets here

        image_file = validated_data.pop("image", None)  # Get the image file if provided

        # Create the course instance - assumes 'instructor' is passed via save() in the view
        # e.g., serializer.save(instructor=self.request.user)
        try:
            course = Course.objects.create(**validated_data)
        except TypeError as e:
            # This might happen if 'instructor' is missing and required by the model
            # Should be caught by view logic setting the instructor
            raise serializers.ValidationError(
                f"Failed to create course. Missing required data? Error: {e}"
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        # If an image file was uploaded, assign it and save again
        if image_file:
            course.image = image_file
            course.save(update_fields=["image", "updated_at"])  # Optimize save

        return course

    def update(self, instance, validated_data):
        """
        Handles updating an existing Course instance.
        Allows *Admin* to change the instructor via instructor_id.
        Handles image updates (new file) or removal (null).
        """
        # Handle instructor change *only if* admin and instructor_id is provided
        # Note: 'instructor_id' field uses source='instructor', so validated_data contains 'instructor' User object
        new_instructor = validated_data.pop("instructor", None)
        requesting_user = self.context["request"].user

        if new_instructor is not None:
            if requesting_user.is_staff:
                # Admin is allowed to change instructor
                instance.instructor = new_instructor
            else:
                # Non-admin attempting to change instructor - raise error or ignore
                raise PermissionDenied("Only Admins can change the course instructor.")
        elif (
            "instructor_id" in self.initial_data
            and self.initial_data["instructor_id"] is None
        ):
            # Handle explicit request to set instructor to null (if allowed by model)
            if requesting_user.is_staff:
                if Course._meta.get_field("instructor").null:
                    instance.instructor = None
                else:
                    raise serializers.ValidationError(
                        {
                            "instructor_id": "Instructor cannot be set to null for this course."
                        }
                    )
            else:
                raise PermissionDenied("Only Admins can change the course instructor.")

        # Handle image update/removal
        # Use Ellipsis as a sentinel to differentiate 'not provided' from 'provided as null'
        image_update = validated_data.pop("image", Ellipsis)
        if image_update is not Ellipsis:
            # 'image' key was present in the request data (could be a File or null)
            instance.image = image_update  # Assign the new File object or None

        # Update remaining fields provided in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.save()  # Let model's save() handle updated_at
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return instance
