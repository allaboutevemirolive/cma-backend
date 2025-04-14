# src/apps/users/tests.py

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.profiles.models import Profile  # Needed to check roles

User = get_user_model()


class UserApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # --- Create Users ---
        cls.admin_user = User.objects.create_superuser(
            username="usertestadmin",
            password="password123",
            email="usertestadmin@test.com",
        )
        cls.instructor_user = User.objects.create_user(
            username="usertestinstructor",
            password="password123",
            email="usertestinstr@test.com",
        )
        cls.instructor_user.refresh_from_db()
        cls.instructor_user.profile.role = Profile.Role.INSTRUCTOR
        cls.instructor_user.profile.save()

        cls.student_user = User.objects.create_user(
            username="userteststudent",
            password="password123",
            email="userteststudent@test.com",
        )
        cls.student_user.refresh_from_db()
        cls.student_user.profile.role = Profile.Role.STUDENT
        cls.student_user.profile.save()

        # User to be deleted by admin
        cls.user_to_delete = User.objects.create_user(
            username="deleteme", password="password123", email="deleteme@test.com"
        )
        cls.user_to_delete.refresh_from_db()
        cls.user_to_delete.profile.role = Profile.Role.STUDENT
        cls.user_to_delete.profile.save()

        # --- URLs ---
        cls.register_url = reverse("user-register")
        cls.token_url = reverse("token_obtain_pair")
        cls.refresh_url = reverse("token_refresh")
        cls.me_url = reverse("current-user")  # Assuming name='current-user'
        cls.admin_user_list_url = reverse("admin-user-list")
        cls.admin_user_detail_url = lambda pk: reverse(
            "admin-user-detail", kwargs={"pk": pk}
        )

    def _get_jwt_header(self, user):
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    def _get_tokens(self, username, password):
        response = self.client.post(
            self.token_url, {"username": username, "password": password}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data  # {"refresh": "...", "access": "..."}

    # --- Registration Tests ---
    def test_register_student_success(self):
        data = {
            "username": "new_reg_student",
            "email": "reg_student@test.com",
            "password": "password123",
            "password2": "password123",
            "role": "student",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(username="new_reg_student")
        self.assertEqual(user.profile.role, Profile.Role.STUDENT)

    def test_register_instructor_success(self):
        data = {
            "username": "new_reg_instructor",
            "email": "reg_instructor@test.com",
            "password": "password123",
            "password2": "password123",
            "role": "instructor",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(username="new_reg_instructor")
        self.assertEqual(user.profile.role, Profile.Role.INSTRUCTOR)

    def test_register_admin_role_fails(self):
        data = {
            "username": "wannabe_admin",
            "email": "wannabe@test.com",
            "password": "password123",
            "password2": "password123",
            "role": "admin",  # Trying to register as admin
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot register as Admin", str(response.data))

    def test_register_duplicate_username(self):
        data = {
            "username": "userteststudent",  # Existing username
            "email": "unique@test.com",
            "password": "password123",
            "password2": "password123",
            "role": "student",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A user with that username already exists.", str(response.data))

    def test_register_duplicate_email(self):
        data = {
            "username": "unique_user",
            "email": "userteststudent@test.com",  # Existing email
            "password": "password123",
            "password2": "password123",
            "role": "student",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email already exists", str(response.data))

    def test_register_password_mismatch(self):
        data = {
            "username": "mismatch_user",
            "email": "mismatch@test.com",
            "password": "password123",
            "password2": "password456",  # Mismatch
            "role": "student",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Password fields didn't match", str(response.data))

    # --- Authentication Tests ---
    def test_login_success(self):
        tokens = self._get_tokens("userteststudent", "password123")
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_login_fail_wrong_password(self):
        response = self.client.post(
            self.token_url,
            {"username": "userteststudent", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_success(self):
        tokens = self._get_tokens("userteststudent", "password123")
        refresh_token = tokens["refresh"]
        response = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        # Optionally check if the new access token is different from the old one

    def test_token_refresh_fail_invalid_token(self):
        response = self.client.post(
            self.refresh_url, {"refresh": "invalidtoken"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Current User Endpoint ---
    def test_get_current_user_me(self):
        tokens = self._get_tokens("userteststudent", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        response = self.client.get(self.me_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "userteststudent")
        self.assertEqual(response.data["profile"]["role"], "student")

    def test_get_current_user_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Admin User Management ---
    def test_admin_list_users_success(self):
        tokens = self._get_tokens("usertestadmin", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        response = self.client.get(self.admin_user_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response contains multiple users (at least admin, instructor, student, deleteme)
        self.assertGreaterEqual(response.data["count"], 4)

    def test_admin_list_users_non_admin_forbidden(self):
        tokens = self._get_tokens("usertestinstructor", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        response = self.client.get(self.admin_user_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        tokens_student = self._get_tokens("userteststudent", "password123")
        headers_student = {"HTTP_AUTHORIZATION": f"Bearer {tokens_student['access']}"}
        response_student = self.client.get(self.admin_user_list_url, **headers_student)
        self.assertEqual(response_student.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete_user_success(self):
        tokens = self._get_tokens("usertestadmin", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        user_to_delete_pk = self.user_to_delete.pk
        url = self.admin_user_detail_url(user_to_delete_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify user is actually deleted
        self.assertFalse(User.objects.filter(pk=user_to_delete_pk).exists())

    def test_admin_delete_superuser_fail(self):
        tokens = self._get_tokens("usertestadmin", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        superuser_pk = (
            self.admin_user.pk
        )  # Trying to delete self (or another superuser)
        url = self.admin_user_detail_url(superuser_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot delete superuser", str(response.data))
        # Verify superuser still exists
        self.assertTrue(User.objects.filter(pk=superuser_pk).exists())

    def test_admin_delete_user_non_admin_forbidden(self):
        tokens = self._get_tokens("usertestinstructor", "password123")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        url = self.admin_user_detail_url(self.user_to_delete.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
