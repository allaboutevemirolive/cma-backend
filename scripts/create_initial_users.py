#!/usr/bin/env python3
import os
import sys
import django
from pathlib import Path

# --- Adjust path to find Django project ---
# Add the 'src' directory (containing manage.py and 'config'/'apps') to the Python path
# Assumes the script is run from the project root (/app in the container) when using 'manage.py runscript'
# Or that the WORKDIR is /app when running directly `python /app/scripts/create_initial_users.py`
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent  # Goes up one level from /app/scripts to /app
sys.path.append(str(PROJECT_ROOT))

# --- Setup Django Environment ---
# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    print(
        "Ensure DJANGO_SETTINGS_MODULE is set correctly and dependencies are installed."
    )
    sys.exit(1)

# --- Import models AFTER Django setup ---
try:
    from django.contrib.auth import get_user_model
    from apps.profiles.models import Profile
    from django.db import IntegrityError
    from django.core.management.base import CommandError  # For potential errors
except ImportError as e:
    print(f"Error importing Django modules: {e}")
    print("Make sure Django is installed and the project structure is correct.")
    sys.exit(1)

User = get_user_model()

# --- Configuration (Use Environment Variables or Defaults) ---
# Superuser
SUPERUSER_USERNAME = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
SUPERUSER_EMAIL = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv(
    "DJANGO_SUPERUSER_PASSWORD", "aabc@123a"
)  # CHANGE IN PRODUCTION/SECURE ENV

# Instructor
INSTRUCTOR_USERNAME = os.getenv("DEFAULT_INSTRUCTOR_USERNAME", "instructor1")
INSTRUCTOR_EMAIL = os.getenv("DEFAULT_INSTRUCTOR_EMAIL", "instructor1@example.com")
INSTRUCTOR_PASSWORD = os.getenv(
    "DEFAULT_INSTRUCTOR_PASSWORD", "aabc@123a"
)  # CHANGE IN PRODUCTION/SECURE ENV

# Student
STUDENT_USERNAME = os.getenv("DEFAULT_STUDENT_USERNAME", "student1")
STUDENT_EMAIL = os.getenv("DEFAULT_STUDENT_EMAIL", "student1@example.com")
STUDENT_PASSWORD = os.getenv(
    "DEFAULT_STUDENT_PASSWORD", "aabc@123a"
)  # CHANGE IN PRODUCTION/SECURE ENV


# --- Helper Function to Create User + Profile ---
def create_user_with_profile(username, email, password, role):
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=False,  # Regular users are not staff
            is_superuser=False,
        )
        # Profile *should* be created by the post_save signal in profiles.models
        # We just need to ensure the role is set correctly.
        # The signal sets default='student', so we override for instructor.
        # The signal might also set role='admin' if is_staff=True, but we ensure is_staff=False here.
        try:
            user.profile.role = role
            user.profile.save()
            print(f"Successfully created user '{username}' with role '{role}'.")
            return user
        except Profile.DoesNotExist:
            print(
                f"Warning: Profile signal didn't run for user '{username}'. Creating profile manually."
            )
            Profile.objects.create(user=user, role=role)
            print(
                f"Successfully created user '{username}' with role '{role}' (manual profile)."
            )
            return user
        except Exception as e:
            print(f"Error setting profile role for user '{username}': {e}")
            # User exists but profile might be wrong, consider deleting or manual fix
            return None  # Indicate profile issue

    except IntegrityError:
        print(
            f"User '{username}' or email '{email}' already exists. Skipping creation."
        )
        # Optionally, try to fetch and update the existing user's profile role if needed
        try:
            user = User.objects.get(username=username)
            if not hasattr(user, "profile"):
                print(f"Existing user '{username}' is missing a profile. Creating one.")
                Profile.objects.create(user=user, role=role)
            elif user.profile.role != role:
                print(f"Updating existing user '{username}' profile role to '{role}'.")
                user.profile.role = role
                user.profile.save()
            else:
                print(f"Existing user '{username}' already has correct role '{role}'.")
            return user  # Return existing user
        except User.DoesNotExist:
            print(
                f"IntegrityError occurred but could not find user '{username}' by username."
            )
            return None  # Cannot proceed
        except Exception as e:
            print(f"Error handling existing user '{username}': {e}")
            return None  # Cannot proceed

    except Exception as e:
        print(f"An unexpected error occurred creating user '{username}': {e}")
        return None


# --- Main Execution ---
print("--- Starting Initial User Creation ---")

# 1. Create Superuser
print(f"\nAttempting to create Superuser: {SUPERUSER_USERNAME}...")
if not User.objects.filter(username=SUPERUSER_USERNAME).exists():
    try:
        admin_user = User.objects.create_superuser(
            username=SUPERUSER_USERNAME,
            email=SUPERUSER_EMAIL,
            password=SUPERUSER_PASSWORD,
        )
        # Profile post_save signal should automatically set role to 'admin'
        # because is_staff=True for superusers. We verify.
        try:
            admin_user.refresh_from_db()  # Ensure relations are loaded
            if (
                hasattr(admin_user, "profile")
                and admin_user.profile.role == Profile.Role.ADMIN
            ):
                print(
                    f"Successfully created Superuser '{SUPERUSER_USERNAME}' with Admin profile."
                )
            else:
                print(
                    f"Warning: Superuser '{SUPERUSER_USERNAME}' created, but profile role might not be 'admin'. Check signals/profile logic."
                )
                # Attempt to fix if needed
                if not hasattr(admin_user, "profile"):
                    print("-> Creating missing profile...")
                    Profile.objects.create(user=admin_user, role=Profile.Role.ADMIN)
                elif admin_user.profile.role != Profile.Role.ADMIN:
                    print("-> Correcting profile role...")
                    admin_user.profile.role = Profile.Role.ADMIN
                    admin_user.profile.save()

        except Exception as e:
            print(
                f"Error checking/updating profile for superuser '{SUPERUSER_USERNAME}': {e}"
            )

    except IntegrityError:
        print(
            f"Superuser '{SUPERUSER_USERNAME}' or email '{SUPERUSER_EMAIL}' already exists."
        )
    except Exception as e:
        print(
            f"An unexpected error occurred creating superuser '{SUPERUSER_USERNAME}': {e}"
        )
else:
    print(f"Superuser '{SUPERUSER_USERNAME}' already exists. Skipping creation.")

# 2. Create Instructor
print(f"\nAttempting to create Instructor: {INSTRUCTOR_USERNAME}...")
create_user_with_profile(
    username=INSTRUCTOR_USERNAME,
    email=INSTRUCTOR_EMAIL,
    password=INSTRUCTOR_PASSWORD,
    role=Profile.Role.INSTRUCTOR,  # Explicitly request 'instructor' role
)

# 3. Create Student
print(f"\nAttempting to create Student: {STUDENT_USERNAME}...")
create_user_with_profile(
    username=STUDENT_USERNAME,
    email=STUDENT_EMAIL,
    password=STUDENT_PASSWORD,
    role=Profile.Role.STUDENT,  # Explicitly request 'student' role
)


print("\n--- Initial User Creation Finished ---")
sys.exit(0)
