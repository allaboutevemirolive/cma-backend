# src/apps/enrollments/tests.py

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

# Import necessary models
from apps.courses.models import Course
from apps.profiles.models import Profile # Ensure Profile model is imported
from .models import Enrollment

User = get_user_model()


class EnrollmentApiTests(APITestCase):
    """
    Test suite for the Enrollment API endpoints (/api/enrollments/).
    Covers permissions, create, list, retrieve, and delete actions for MVP.
    Updates are explicitly tested as disabled.
    """
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole test class."""
        # --- Create Users with specific roles ---
        cls.admin_user = User.objects.create_superuser(
            username="enroll_admin", password="password123", email="enroll_admin@test.com"
        )
        # Profile signal handles setting role to 'admin'

        cls.instructor_user = User.objects.create_user(
            username="enroll_instructor", password="password123", email="enroll_instr@test.com"
        )
        cls.instructor_user.refresh_from_db() # Load related profile created by signal
        Profile.objects.update_or_create(user=cls.instructor_user, defaults={'role': Profile.Role.INSTRUCTOR})


        cls.student_user = User.objects.create_user(
            username="enroll_student", password="password123", email="enroll_student@test.com"
        )
        cls.student_user.refresh_from_db()
        # Ensure student role, even if default
        Profile.objects.update_or_create(user=cls.student_user, defaults={'role': Profile.Role.STUDENT})


        cls.other_student_user = User.objects.create_user(
            username="enroll_student2", password="password123", email="enroll_student2@test.com"
        )
        cls.other_student_user.refresh_from_db()
        Profile.objects.update_or_create(user=cls.other_student_user, defaults={'role': Profile.Role.STUDENT})


        # --- Create Courses ---
        cls.course1 = Course.objects.create(
            title="Enrollment Test Course 1", description="...", price="15.00",
            instructor=cls.instructor_user, status=Course.Status.ACTIVE
        )
        cls.course2 = Course.objects.create(
            title="Enrollment Test Course 2", description="...", price="25.00",
            instructor=cls.instructor_user, status=Course.Status.ACTIVE
        )
        cls.inactive_course = Course.objects.create(
            title="Inactive Course", description="...", price="5.00",
            instructor=cls.instructor_user, status=Course.Status.INACTIVE
        )


        # --- Create Initial Enrollment ---
        cls.enrollment1_student1_course1 = Enrollment.objects.create(
            student=cls.student_user,
            course=cls.course1
        )

        # --- URLs ---
        cls.list_create_url = reverse("enrollment-list")
        cls.detail_url = lambda pk: reverse("enrollment-detail", kwargs={"pk": pk})

    def _get_jwt_header(self, user):
        """Helper to generate JWT authorization header."""
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    # === Authentication Tests ===
    def test_list_enrollments_unauthenticated(self):
        """GET /api/enrollments/ requires authentication."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_enrollment_unauthenticated(self):
        """POST /api/enrollments/ requires authentication."""
        data = {"course_id": self.course1.pk}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === Permission & Logic Tests (RBAC for Enrollments) ===

    # -- List Enrollments --
    def test_list_enrollments_student_sees_only_own(self):
        """Students should only see their own enrollments."""
        # Create another enrollment for a different student for contrast
        Enrollment.objects.create(student=self.other_student_user, course=self.course1)

        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.list_create_url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1, "Student should only see 1 enrollment")
        self.assertEqual(response.data["results"][0]["id"], self.enrollment1_student1_course1.id)
        self.assertEqual(response.data["results"][0]["student"]["id"], self.student_user.id)

    def test_list_enrollments_instructor_sees_none_by_default(self):
        """Instructors do not see any enrollments via the base list endpoint (as per MVP)."""
        headers = self._get_jwt_header(self.instructor_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0, "Instructor should see 0 enrollments by default")

    def test_list_enrollments_admin_sees_all(self):
        """Admins should see all non-deleted enrollments."""
        enrollment2 = Enrollment.objects.create(student=self.other_student_user, course=self.course1)
        headers = self._get_jwt_header(self.admin_user)
        response = self.client.get(self.list_create_url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2, "Admin should see all enrollments")
        enrollment_ids = {e['id'] for e in response.data['results']}
        self.assertIn(self.enrollment1_student1_course1.id, enrollment_ids)
        self.assertIn(enrollment2.id, enrollment_ids)

    # -- Create Enrollment (Enroll) --
    def test_create_enrollment_student_success(self):
        """Students (non-instructors) can enroll in a course."""
        headers = self._get_jwt_header(self.student_user)
        data = {"course_id": self.course2.pk} # Enroll student in course 2
        response = self.client.post(self.list_create_url, data, format="json", **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(
            Enrollment.objects.filter(student=self.student_user, course=self.course2).exists(),
            "Enrollment record not created in DB"
        )
        self.assertEqual(response.data["student"]["id"], self.student_user.id)
        self.assertEqual(response.data["course"]["id"], self.course2.id)
        self.assertEqual(response.data["status"], Enrollment.Status.ACTIVE) # Verify default status

    def test_create_enrollment_instructor_forbidden(self):
        """Instructors cannot enroll in courses (Test Validation Message)."""
        headers = self._get_jwt_header(self.instructor_user)
        data = {"course_id": self.course1.pk}
        response = self.client.post(self.list_create_url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for the specific error message from the serializer
        expected_error = "Users with role 'instructor' cannot enroll in courses."
        # DRF wraps validation errors in a list under 'non_field_errors' by default when raised from validate()
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(len(response.data['non_field_errors']), 1)
        self.assertEqual(str(response.data['non_field_errors'][0]), expected_error)

    def test_create_enrollment_admin_forbidden(self):
        """Admins cannot enroll via this endpoint (Test Validation Message)."""
        headers = self._get_jwt_header(self.admin_user)
        data = {"course_id": self.course1.pk}
        response = self.client.post(self.list_create_url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for the specific error message for the admin role
        expected_error = "Users with role 'admin' cannot enroll in courses."
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(len(response.data['non_field_errors']), 1)
        self.assertEqual(str(response.data['non_field_errors'][0]), expected_error)


    def test_create_enrollment_already_enrolled_forbidden(self):
        """Users cannot enroll in the same course twice."""
        headers = self._get_jwt_header(self.student_user)
        data = {"course_id": self.course1.pk} # student_user already enrolled in course1
        response = self.client.post(self.list_create_url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", str(response.data))

    # -- Retrieve Enrollment Details --
    def test_retrieve_enrollment_owner_student_success(self):
        """The student owning the enrollment can retrieve its details."""
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.enrollment1_student1_course1.id)

    def test_retrieve_enrollment_other_student_not_found(self):
        """A student cannot retrieve enrollment details owned by another student."""
        headers = self._get_jwt_header(self.other_student_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk) # Owned by student_user
        response = self.client.get(url, **headers)
        # Viewset's get_queryset filters this out
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_enrollment_admin_success(self):
        """Admins can retrieve details of any enrollment."""
        headers = self._get_jwt_header(self.admin_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.enrollment1_student1_course1.id)

    def test_retrieve_enrollment_instructor_not_found(self):
        """Instructors cannot retrieve enrollments via this detail endpoint (MVP)."""
        headers = self._get_jwt_header(self.instructor_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        response = self.client.get(url, **headers)
        # Viewset's get_queryset filters this out
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # -- Update Enrollment (Disabled in MVP) --
    def test_update_enrollment_methods_disabled(self):
        """PUT and PATCH methods are disabled for enrollments."""
        student_headers = self._get_jwt_header(self.student_user)
        admin_headers = self._get_jwt_header(self.admin_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        data = {"status": "completed"} # Arbitrary data

        # Student attempt (should fail permission first)
        response_put_student = self.client.put(url, data, format="json", **student_headers)
        response_patch_student = self.client.patch(url, data, format="json", **student_headers)
        # Based on get_permissions, IsAdminUser permission fails for student -> 403
        self.assertEqual(response_put_student.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_patch_student.status_code, status.HTTP_403_FORBIDDEN)

        # Admin attempt (should pass permission, but hit method override)
        response_put_admin = self.client.put(url, data, format="json", **admin_headers)
        response_patch_admin = self.client.patch(url, data, format="json", **admin_headers)
        # View explicitly returns 405
        self.assertEqual(response_put_admin.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch_admin.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    # -- Delete Enrollment (Unenroll) --
    def test_delete_enrollment_owner_student_success(self):
        """The student owning the enrollment can delete (unenroll) it."""
        target_pk = self.enrollment1_student1_course1.pk
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(target_pk)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify soft delete
        self.assertTrue(Enrollment.all_objects.get(pk=target_pk).is_deleted)
        with self.assertRaises(Enrollment.DoesNotExist):
            Enrollment.objects.get(pk=target_pk) # Check default manager

    def test_delete_enrollment_other_student_not_found(self):
        """A student cannot delete an enrollment owned by another student."""
        headers = self._get_jwt_header(self.other_student_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        response = self.client.delete(url, **headers)
        # Viewset's get_queryset filters this object out for this user -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_enrollment_admin_success(self):
        """Admins can delete any enrollment."""
        target_pk = self.enrollment1_student1_course1.pk
        headers = self._get_jwt_header(self.admin_user)
        url = self.detail_url(target_pk)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify soft delete
        self.assertTrue(Enrollment.all_objects.get(pk=target_pk).is_deleted)

    def test_delete_enrollment_instructor_not_found(self):
        """Instructors cannot delete enrollments via this endpoint (MVP)."""
        headers = self._get_jwt_header(self.instructor_user)
        url = self.detail_url(self.enrollment1_student1_course1.pk)
        response = self.client.delete(url, **headers)
        # Viewset's get_queryset filters this object out for this user -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
