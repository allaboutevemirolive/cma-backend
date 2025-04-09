# backend/courses/serializers.py

from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    # Optional: Make status readable in responses but writable with internal value
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'price',
            'instructor_id',
            'status',
            'status_display', # Show readable status
            'image_url',
            'created_at',
            'updated_at',
            # Exclude soft delete fields from default API output
            # 'is_deleted',
            # 'deleted_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'status_display')

        # Basic Input Validation (DRF handles required, max_length, etc. based on model)
        extra_kwargs = {
            'title': {'required': True, 'allow_blank': False},
            'description': {'required': True, 'allow_blank': False},
            'price': {'required': True, 'min_value': 0},
            'instructor_id': {'required': True},
            'status': {'required': False}, # Default is 'active'
        }

    # Optional: Add more specific validation if needed
    # def validate_title(self, value):
    #     if len(value) < 5:
    #         raise serializers.ValidationError("Title must be at least 5 characters long.")
    #     return value
