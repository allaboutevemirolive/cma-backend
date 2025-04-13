# src/apps/profiles/models.py
from django.db import models
from django.conf import settings # To link to the AUTH_USER_MODEL
from django.utils import timezone
from django.db.models.signals import post_save # To automatically create profiles
from django.dispatch import receiver          # To receive the signal

class Profile(models.Model):
    """
    Extends the base Django User model to add role, status, and potentially
    other profile-specific information for the learning platform.
    """
    class Role(models.TextChoices):
        """Defines the possible roles a user can have on the platform."""
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin' # Represents staff/superusers via profile

    class Status(models.TextChoices):
        """Defines the account status of a user."""
        ACTIVE = 'active', 'Active'      # User can log in and interact
        INACTIVE = 'inactive', 'Inactive'  # User account is disabled by admin
        PENDING = 'pending', 'Pending'    # User needs to take action (e.g., email verification)
        # Add other statuses if needed, e.g., SUSPENDED

    # --- Core Fields ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,   # If the User is deleted, delete the Profile too
        related_name='profile',     # How to access profile from user instance (user.profile)
        primary_key=True,           # Use the user's ID as the primary key for this table
        help_text="The user this profile belongs to."
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,       # Default role for new users
        blank=False,
        null=False,
        help_text="User role determining permissions and capabilities within the platform."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,      # Default status (change to PENDING if verification needed)
        blank=False,
        null=False,
        help_text="Current status of the user's account."
    )
    # --- Optional Profile Fields (Uncomment and add as needed) ---
    # bio = models.TextField(blank=True, help_text="Short user biography.")
    # avatar_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL to the user's avatar image.")
    # date_of_birth = models.DateField(blank=True, null=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the profile was created (usually same as user creation)."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the profile was last updated."
    )

    # --- Soft Delete Fields (Optional - uncomment if needed for profiles) ---
    # is_deleted = models.BooleanField(
    #     default=False,
    #     help_text="Flag indicating if the profile has been soft-deleted."
    # )
    # deleted_at = models.DateTimeField(
    #     blank=True,
    #     null=True,
    #     help_text="Timestamp when the profile was soft-deleted."
    # )

    # --- Managers (Optional - uncomment if using soft delete) ---
    # objects = ProfileManager() # Custom manager for soft delete
    # all_objects = models.Manager()

    # --- Meta Options ---
    class Meta:
        ordering = ['user__username'] # Default ordering by username
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    # --- Instance Methods ---
    def __str__(self):
        """String representation of the Profile model."""
        return f"{self.user.username}'s Profile ({self.get_role_display()})"

    # --- Optional: Soft Delete Methods (uncomment if using soft delete) ---
    # def soft_delete(self):
    #     """Marks the instance as deleted."""
    #     if not self.is_deleted:
    #         self.is_deleted = True
    #         self.deleted_at = timezone.now()
    #         self.save()

    # def restore(self):
    #     """Restores a soft-deleted instance."""
    #     if self.is_deleted:
    #         self.is_deleted = False
    #         self.deleted_at = None
    #         self.save()

# --- Signal Receiver ---
# This function will run automatically *after* a User object is saved.
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Creates or updates the user profile when a User instance is saved.
    - If the user is newly created, a profile is created with default values.
    - If the user exists, their profile is saved (useful if profile fields
      depend on user fields like is_staff).
    """
    if created:
        # If the user was just created, create a corresponding profile
        Profile.objects.create(user=instance)
        print(f"Profile created for new user: {instance.username}")
    else:
        # If the user existed and was updated, ensure their profile is saved.
        # This handles cases where the profile might not have been created
        # previously (e.g., users created before the profile model existed)
        # or if profile logic depends on user flags.
        try:
            instance.profile.save()
            print(f"Profile updated for existing user: {instance.username}")
        except Profile.DoesNotExist:
            # Handle case where profile somehow doesn't exist for an existing user
            Profile.objects.create(user=instance)
            print(f"Profile created for existing user missing one: {instance.username}")

    # Optional: Update role based on staff/superuser status after profile exists/is saved
    if instance.is_staff or instance.is_superuser:
        if instance.profile.role != Profile.Role.ADMIN:
            instance.profile.role = Profile.Role.ADMIN
            instance.profile.save()
            print(f"Role updated to ADMIN for staff user: {instance.username}")
    # You might add logic here to sync role from Django Groups if you use them extensively
    # elif instance.groups.filter(name='Instructors').exists():
    #      if instance.profile.role != Profile.Role.INSTRUCTOR:
    #          instance.profile.role = Profile.Role.INSTRUCTOR
    #          instance.profile.save()
