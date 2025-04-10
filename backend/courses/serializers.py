# backend/courses/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User # Optional: Useful for validating instructor_id if changed to ForeignKey
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model. Handles conversion between Course instances
    and JSON representations for the API.
    """

    # --- Read-only Computed/Related Fields ---
    # Provides a human-readable version of the status field.
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Optional: If you want to explicitly show the instructor's username (assuming instructor_id maps to a User)
    # This requires instructor_id to be a ForeignKey or adding custom logic.
    # For now, we'll stick to instructor_id as required.
    # instructor_username = serializers.SerializerMethodField(read_only=True)

    # The 'image' field using ImageField handles both URL generation on read
    # and file upload handling (multipart/form-data) on write.
    # The URL generated will be relative to MEDIA_URL.

    class Meta:
        model = Course
        # Define the fields to include in the API representation.
        fields = [
            'id',               # Primary key (read-only by default)
            'title',            # Course title (string)
            'description',      # Course description (text)
            'price',            # Course price (decimal)
            'instructor_id',    # ID of the instructor (integer)
            # 'instructor_username', # Uncomment if using SerializerMethodField above
            'status',           # Course status ('active'/'inactive') - writeable
            'status_display',   # Read-only display version of status
            'image',            # Image field (handles upload and URL)
            'created_at',       # Timestamp (read-only)
            'updated_at',       # Timestamp (read-only)
            # We generally exclude soft-delete internal fields from the main API output
            # 'is_deleted',
            # 'deleted_at',
        ]

        # --- Read-Only Fields ---
        # Fields that should not be set directly via the API input.
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'status_display',
            # 'instructor_username', # Uncomment if using SerializerMethodField above
        )

        # --- Field-Level Validation & Options (Optional) ---
        # Define extra constraints or options for specific fields.
        # Many constraints (like required, max_length) are automatically inferred
        # from the model definition unless overridden here.
        extra_kwargs = {
            'title': {
                'required': True, # Explicitly state requirement (though default for non-blank model field)
                'allow_blank': False,
                'error_messages': { # Custom error messages
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
                # DRF DecimalField automatically validates based on model's max_digits/decimal_places
                # You can add min_value if needed:
                # 'min_value': 0.00,
                'error_messages': {
                    'required': 'Course price is required.',
                    'invalid': 'Enter a valid price.',
                }
            },
            'instructor_id': {
                'required': True,
                'error_messages': {
                    'required': 'Instructor ID is required.',
                    'invalid': 'Enter a valid integer for the instructor ID.',
                }
                # Add custom validation below if needed (e.g., check if user exists)
            },
            'status': {
                'required': False, # Defaults to 'active' in the model
            },
            'image': {
                'required': False, # Image is optional
                'allow_null': True,
            }
        }

    # --- Custom Validation Methods (Optional) ---

    def validate_price(self, value):
        """
        Example: Ensure the price is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_instructor_id(self, value):
        """
        Example: Check if a User with the given ID actually exists.
        This is recommended if not using a ForeignKey.
        """
        try:
            # Attempt to get the user. Replace User with your actual User model if different.
            # This assumes the default Django User model.
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"No user found with ID {value}.")
        # Optional: Check if the user is in the 'Instructors' group
        # user = User.objects.get(pk=value)
        # if not user.groups.filter(name='Instructors').exists() and not user.is_staff:
        #     raise serializers.ValidationError(f"User with ID {value} is not an instructor or admin.")
        return value

    # --- Custom Method for SerializerMethodField (Optional) ---
    # def get_instructor_username(self, obj):
    #     """
    #     Returns the username of the instructor.
    #     Requires fetching the User object.
    #     """
    #     try:
    #         user = User.objects.get(pk=obj.instructor_id)
    #         return user.username
    #     except User.DoesNotExist:
    #         return None # Or "N/A", or raise an error depending on requirements


    # --- Object-Level Validation (Optional) ---
    # def validate(self, data):
    #     """
    #     Example: Perform validation that requires access to multiple fields.
    #     """
    #     # Example: Check if title and description are the same (unlikely scenario, just for demo)
    #     # if 'title' in data and 'description' in data and data['title'] == data['description']:
    #     #     raise serializers.ValidationError("Title and description cannot be the same.")
    #     return data

    # --- Create/Update Method Overrides (Optional) ---
    # Generally not needed for simple ModelSerializers unless you have
    # complex logic, like handling nested serializers or specific side effects.
    # def create(self, validated_data):
    #     # Custom logic before creating the instance
    #     instance = super().create(validated_data)
    #     # Custom logic after creating the instance
    #     return instance
    #
    # def update(self, instance, validated_data):
    #     # Custom logic before updating the instance
    #     instance = super().update(instance, validated_data)
    #     # Custom logic after updating the instance
    #     return instance
