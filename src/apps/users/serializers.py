# src/apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User # Or your custom user model
from apps.profiles.models import Profile # Import Profile model

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('role', 'status', 'created_at', 'updated_at') # Add fields as needed

class UserSerializer(serializers.ModelSerializer):
    # Nest the profile serializer
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        # Include 'profile' in fields
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'profile')
        # exclude = ('password',) # Exclude sensitive fields
