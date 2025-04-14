# src/apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from apps.profiles.models import Profile # Import Profile

User = get_user_model()

# Keep existing ProfileSerializer if used by UserSerializer
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('role', 'status') # Minimal fields needed

# Keep existing UserSerializer for general display
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'profile')

# New Serializer for Registration
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    # Add role field for registration
    role = serializers.ChoiceField(choices=Profile.Role.choices, write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': True} # Make email mandatory
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        # Optional: Validate email format more strictly if needed
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        if User.objects.filter(username=attrs['username']).exists():
             raise serializers.ValidationError({"username": "Username already exists."})
        # Prevent registering as Admin via API
        if attrs.get('role') == Profile.Role.ADMIN:
            raise serializers.ValidationError({"role": "Cannot register as Admin via API."})
        return attrs

    def create(self, validated_data):
        # Use transaction to ensure user and profile created together
        with transaction.atomic():
            role = validated_data.pop('role')
            validated_data.pop('password2') # Remove confirmation password
            user = User.objects.create_user( # Use create_user to handle password hashing
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                is_staff=False, # Ensure not staff by default
                is_superuser=False
            )
            # Profile should be created automatically by the signal in profiles/models.py
            # But we need to set the role immediately after creation
            try:
                profile = user.profile # Access the profile created by signal
                profile.role = role
                profile.save()
            except Profile.DoesNotExist:
                # Fallback if signal somehow failed (shouldn't happen ideally)
                Profile.objects.create(user=user, role=role)

        return user

# Serializer for Admin view (might be same as UserSerializer or slightly different)
class AdminUserSerializer(serializers.ModelSerializer):
     profile = ProfileSerializer(read_only=True)
     class Meta:
         model = User
         # Exclude sensitive fields, show relevant info for admin
         fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'profile')
