# src/apps/profiles/tests.py

# from django.test import TestCase

# No API endpoint tests needed for Profiles in MVP.
# Model tests could be added here if desired.

# Example basic model test (optional):
# from django.contrib.auth import get_user_model
# from .models import Profile
#
# User = get_user_model()
#
# class ProfileModelTests(TestCase):
#
#     def test_profile_creation_signal(self):
#         """Test that a Profile is automatically created when a User is created."""
#         user = User.objects.create_user(username='testsignaluser', password='password')
#         self.assertTrue(hasattr(user, 'profile'))
#         self.assertIsInstance(user.profile, Profile)
#         self.assertEqual(user.profile.role, Profile.Role.STUDENT) # Default role
#
#     def test_profile_role_update_for_staff(self):
#         """Test that profile role is updated to Admin for staff users."""
#         user = User.objects.create_user(username='teststaffuser', password='password', is_staff=True)
#         user.save() # Save again to trigger potential update logic in signal if needed
#         user.refresh_from_db() # Refresh to ensure profile relation is loaded
#         self.assertEqual(user.profile.role, Profile.Role.ADMIN)
