# src/apps/enrollments/serializers.py
from rest_framework import serializers
from .models import Enrollment
from apps.users.serializers import UserSerializer # Reuse UserSerializer
from apps.courses.serializers import CourseSerializer # Reuse CourseSerializer

class EnrollmentSerializer(serializers.ModelSerializer):
    # Nested representations for student and course (read-only)
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    # Write-only fields for creating enrollments
    student_id = serializers.IntegerField(write_only=True, required=True)
    course_id = serializers.IntegerField(write_only=True, required=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'course', 'enrollment_date', 'status', 'status_display',
            'created_at', 'updated_at', 'student_id', 'course_id'
        ]
        read_only_fields = ('id', 'enrollment_date', 'created_at', 'updated_at', 'student', 'course', 'status_display')
        extra_kwargs = {
            'status': {'required': False}, # Default is 'active'
        }

    def validate(self, data):
        # Ensure student isn't enrolling themselves in their own course (if applicable)
        # Example check:
        # course = Course.objects.filter(pk=data['course_id']).first()
        # if course and course.instructor_id == data['student_id']:
        #     raise serializers.ValidationError("Instructors cannot enroll in their own courses.")

        # Check for existing non-deleted enrollment
        if Enrollment.objects.filter(student_id=data['student_id'], course_id=data['course_id']).exists():
             raise serializers.ValidationError("User is already enrolled in this course.")

        return data

    def create(self, validated_data):
        # Extract IDs and create the enrollment instance
        # Assumes student_id and course_id are validated and exist
        enrollment = Enrollment.objects.create(**validated_data)
        return enrollment
