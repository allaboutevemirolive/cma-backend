# src/apps/users/serializers.py (or a common location)
from rest_framework import serializers
from django.contrib.auth.models import User # Or your custom user model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name') # Add fields you need
        # exclude = ('password',) # Exclude sensitive fields
