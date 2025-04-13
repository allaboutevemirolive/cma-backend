# src/apps/courses/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model # Best practice to get the User model
from .models import Course
# Assuming UserSerializer is correctly placed and defined
# Adjust the import path if your UserSerializer is elsewhere
from apps.users.serializers import UserSerializer

User = get_user_model() # Get the active User model

class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model. Handles conversion between Course instances
    and JSON representations for the API. Includes nested instructor details
    for reading and accepts instructor_id for writing. Handles image uploads.
    """

    # --- Read-only Computed/Related Fields ---
    # Provides a human-readable version of the status field.
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Nested representation of the instructor for read operations.
    # Uses the UserSerializer defined elsewhere.
    instructor = UserSerializer(read_only=True)

    # --- Write-only Fields ---
    # Accepts the instructor's ID during POST/PUT/PATCH requests.
    # This field is only used for input, not included in the response.
    instructor_id = serializers.IntegerField(
        write_only=True,
        required=True, # Make sure it's provided on creation
        help_text="ID of the user to assign as instructor for this course."
    )

    # The 'image' field using ImageField handles both URL generation on read
    # and file upload handling (multipart/form-data) on write.
    # Setting allow_null=True allows sending 'null' to remove the image on update.
    image = serializers.ImageField(
        required=False, # Image is not mandatory
        allow_null=True, # Allow null input for clearing the image
        help_text="Upload an image file for the course (optional). Send null to remove the existing image."
    )

    class Meta:
        model = Course
        # Define the fields to include in the API representation.
        fields = [
            'id',               # Primary key
            'title',            # Course title
            'description',      # Course description
            'price',            # Course price
            'instructor',       # Nested instructor details (read-only)
            'instructor_id',    # Instructor ID (write-only)
            'status',           # Course status ('active'/'inactive'/'draft')
            'status_display',   # Read-only display version of status
            'image',            # Image field (handles upload/URL/removal)
            'created_at',       # Timestamp
            'updated_at',       # Timestamp
            # Excluded: 'is_deleted', 'deleted_at'
        ]

        # Fields that should not be set directly via the API input on read operations.
        # Note: 'instructor_id' is handled separately by 'write_only=True'.
        read_only_fields = (
            'id',
            'instructor', # The nested object is read-only
            'status_display',
            'created_at',
            'updated_at',
        )

        # Define extra constraints or options for specific fields.
        extra_kwargs = {
            'title': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': 'Course title is required.',
                    'blank': 'Course title cannot be blank.',
                }
            },
            'description': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': 'Course description is required.',
                    'blank': 'Course description cannot be blank.',
                }
            },
            'price': {
                'required': True,
                'error_messages': {
                    'required': 'Course price is required.',
                    'invalid': 'Enter a valid price.',
                }
                # Optional: Add min_value validation here if not using model validator
                # 'min_value': 0.00,
            },
            'status': {
                'required': False, # Defaults to 'draft' in the model
            },
            # 'image' is handled by the explicit ImageField definition above
        }

    # --- Custom Validation Methods ---

    def validate_price(self, value):
        """Ensures the price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_instructor_id(self, value):
        """Checks if a User with the given ID exists and is suitable."""
        try:
            user = User.objects.get(pk=value)
            # Optional: Check if the user has the 'instructor' role or is staff
            # This check assumes you have the Profile model set up correctly.
            # Adjust based on your actual role checking logic (e.g., groups).
            is_instructor = hasattr(user, 'profile') and user.profile.role == 'instructor'
            is_admin = user.is_staff

            if not is_instructor and not is_admin:
                 raise serializers.ValidationError(
                     f"User '{user.username}' (ID: {value}) does not have the 'Instructor' role and is not an admin."
                 )

        except User.DoesNotExist:
            raise serializers.ValidationError(f"No user found with ID {value}.")
        except AttributeError:
             # This might happen if the Profile relationship isn't set up yet for the user
             if not user.is_staff: # Allow admins even if profile access fails temporarily
                raise serializers.ValidationError(f"Could not verify role for user with ID {value}. Profile might be missing.")

        return value # Return the validated ID

    # --- Object Creation and Update Logic ---

    def create(self, validated_data):
        """
        Handles creation of a new Course instance.
        Extracts instructor_id to fetch the User object.
        Handles optional image upload.
        """
        instructor_id = validated_data.pop('instructor_id')
        image_file = validated_data.pop('image', None) # Get the image file if provided

        try:
            instructor = User.objects.get(pk=instructor_id)
        except User.DoesNotExist:
            # This shouldn't happen if validate_instructor_id worked, but belts and braces
            raise serializers.ValidationError({"instructor_id": f"User with ID {instructor_id} not found during creation."})

        # Create the course instance without the image first
        course = Course.objects.create(instructor=instructor, **validated_data)

        # If an image file was uploaded, assign it and save again
        if image_file:
            course.image = image_file
            course.save(update_fields=['image', 'updated_at']) # Optimize save

        return course

    def update(self, instance, validated_data):
        """
        Handles updating an existing Course instance.
        Allows changing the instructor via instructor_id.
        Handles image updates (new file) or removal (null).
        """
        # Handle instructor change if instructor_id is provided
        instructor_id = validated_data.pop('instructor_id', None)
        if instructor_id is not None:
            try:
                instance.instructor = User.objects.get(pk=instructor_id)
            except User.DoesNotExist:
                 raise serializers.ValidationError({"instructor_id": f"User with ID {instructor_id} not found for update."})

        # Handle image update/removal
        # Use Ellipsis as a sentinel to differentiate 'not provided' from 'provided as null'
        image_update = validated_data.pop('image', Ellipsis)
        if image_update is not Ellipsis:
            # 'image' key was present in the request data (could be a File or null)
            instance.image = image_update # Assign the new File object or None

        # Update remaining fields provided in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save() # Let model's save() handle updated_at
        return instance
