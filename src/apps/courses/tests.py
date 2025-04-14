# src/apps/courses/tests.py
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Course
from apps.profiles.models import Profile  # Ensure Profile model is imported

User = get_user_model()


def get_temporary_image_file(temp_file=None):
    """Creates a temporary JPEG image file for testing uploads."""
    img = Image.new("RGB", (10, 10), color="red")
    if temp_file is None:
        # Create a temporary file that persists until explicitly closed
        # This avoids issues with the file disappearing before DRF processes it
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        )  # Keep file after context
    img.save(temp_file.name, format="JPEG")
    temp_file.seek(0)
    # Return the file object itself for DRF test client
    # We need to reopen it for reading in binary mode
    file_obj = open(temp_file.name, "rb")
    # DRF's test client handles SimpleUploadedFile well too
    # return SimpleUploadedFile(
    #     name=temp_file.name.split('/')[-1], # Use just the filename part
    #     content=file_obj.read(),
    #     content_type="image/jpeg"
    # )
    # Returning the file object might be simpler for multipart form data
    return file_obj


class CourseApiTests(APITestCase):
    """
    Test suite for the Course API endpoints (/api/courses/).
    Covers CRUD operations, permissions, soft delete, and file uploads.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole test class."""
        # --- Create Users ---
        cls.admin_user = User.objects.create_superuser(
            "testadmin", "admin@test.com", "password123"
        )
        # Profile signal should set role to 'admin'

        cls.instructor_user = User.objects.create_user(
            "testinstructor", "instructor@test.com", "password123"
        )
        cls.instructor_user.refresh_from_db()
        Profile.objects.update_or_create(
            user=cls.instructor_user, defaults={"role": Profile.Role.INSTRUCTOR}
        )

        cls.other_instructor_user = User.objects.create_user(
            "otherinstructor", "instructor2@test.com", "password123"
        )
        cls.other_instructor_user.refresh_from_db()
        Profile.objects.update_or_create(
            user=cls.other_instructor_user, defaults={"role": Profile.Role.INSTRUCTOR}
        )

        cls.student_user = User.objects.create_user(
            "teststudent", "student@test.com", "password123"
        )
        cls.student_user.refresh_from_db()
        Profile.objects.update_or_create(
            user=cls.student_user, defaults={"role": Profile.Role.STUDENT}
        )

        # --- Create Courses ---
        cls.course1_by_instructor = Course.objects.create(
            title="Test Course 1 by Instructor",
            description="Desc 1",
            price="10.00",
            instructor=cls.instructor_user,
            status=Course.Status.ACTIVE,
        )
        cls.course2_by_admin_as_instructor = Course.objects.create(
            title="Test Course 2 by Admin User",
            description="Desc 2",
            price="20.00",
            instructor=cls.admin_user,
            status=Course.Status.INACTIVE,
        )
        cls.course3_to_delete = Course.objects.create(
            title="Course to Delete",
            description="Will be soft-deleted",
            price="5.00",
            instructor=cls.instructor_user,
            status=Course.Status.ACTIVE,
        )

        # --- URLs ---
        cls.list_create_url = reverse("course-list")
        cls.detail_url = lambda pk: reverse("course-detail", kwargs={"pk": pk})
        cls.restore_url = lambda pk: reverse("course-restore", kwargs={"pk": pk})
        cls.deleted_list_url = reverse("course-deleted-list")

    def _get_jwt_header(self, user):
        """Helper to get JWT token header for a specific user."""
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    # === Authentication Tests ===
    def test_list_courses_unauthenticated(self):
        """GET /api/courses/ requires authentication."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_course_unauthenticated(self):
        """POST /api/courses/ requires authentication."""
        data = {"title": "Fail Create", "description": "Fail", "price": "5.00"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === Permission Tests (RBAC for Courses) ===

    # -- List / Retrieve Permissions --
    def test_list_courses_student_allowed(self):
        """Students can list courses."""
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_list_courses_instructor_allowed(self):
        """Instructors can list courses."""
        headers = self._get_jwt_header(self.instructor_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_list_courses_admin_allowed(self):
        """Admins can list courses."""
        headers = self._get_jwt_header(self.admin_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_retrieve_course_detail_any_authenticated_user_allowed(self):
        """Any authenticated user can retrieve details of a specific course."""
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.course1_by_instructor.title)
        self.assertIn("instructor", response.data)
        self.assertEqual(response.data["instructor"]["id"], self.instructor_user.id)

    # -- Create Permissions --
    def test_create_course_student_forbidden(self):
        """Students cannot create courses."""
        headers = self._get_jwt_header(self.student_user)
        data = {"title": "Student Creation Fail", "description": "...", "price": "5.00"}
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_admin_forbidden(self):
        """Admins cannot create courses via API (as per MVP permissions)."""
        headers = self._get_jwt_header(self.admin_user)
        data = {"title": "Admin Creation Fail", "description": "...", "price": "100.00"}
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_instructor_success(self):
        """Instructors can create courses."""
        headers = self._get_jwt_header(self.instructor_user)
        data = {
            "title": "Instructor Course Create Success",
            "description": "Created by test instructor",
            "price": "55.00",
            "status": Course.Status.DRAFT,
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Course.objects.count(), 4)
        new_course = Course.objects.get(pk=response.data["id"])
        self.assertEqual(new_course.instructor, self.instructor_user)
        self.assertEqual(new_course.status, Course.Status.DRAFT)

    # -- Update (PUT/PATCH) Permissions --
    def test_update_course_student_forbidden(self):
        """Students cannot update courses."""
        headers = self._get_jwt_header(self.student_user)
        data = {"title": "Student Update Fail"}
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_instructor_owns_success(self):
        """Instructors can update their own courses."""
        headers = self._get_jwt_header(self.instructor_user)
        new_title = "Updated By Owner Instructor PATCH"
        data = {"title": new_title, "price": "12.50"}
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course1_by_instructor.refresh_from_db()
        self.assertEqual(self.course1_by_instructor.title, new_title)
        self.assertEqual(float(self.course1_by_instructor.price), 12.50)

    def test_update_course_instructor_does_not_own_forbidden(self):
        """Instructors cannot update courses owned by others."""
        headers = self._get_jwt_header(self.other_instructor_user)
        data = {"title": "Update Fail - Other Instructor"}
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_admin_can_update_any(self):
        """Admins can update any course (including changing instructor)."""
        headers = self._get_jwt_header(self.admin_user)
        new_status = Course.Status.ACTIVE
        data = {"status": new_status, "instructor_id": self.other_instructor_user.id}
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course1_by_instructor.refresh_from_db()
        self.assertEqual(self.course1_by_instructor.status, new_status)
        self.assertEqual(
            self.course1_by_instructor.instructor, self.other_instructor_user
        )

    def test_update_course_instructor_cannot_change_instructor_forbidden(self):
        """Instructors cannot change the instructor field of their own course."""
        headers = self._get_jwt_header(self.instructor_user)
        data = {"instructor_id": self.other_instructor_user.id}
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.course1_by_instructor.refresh_from_db()
        self.assertEqual(self.course1_by_instructor.instructor, self.instructor_user)

    # -- Delete Permissions --
    def test_delete_course_student_forbidden(self):
        """Students cannot delete courses."""
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.course3_to_delete.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_course_instructor_owns_success(self):
        """Instructors can delete their own courses."""
        headers = self._get_jwt_header(self.instructor_user)
        target_course_pk = self.course3_to_delete.pk
        url = self.detail_url(target_course_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        deleted_course = Course.all_objects.get(pk=target_course_pk)
        self.assertTrue(deleted_course.is_deleted)
        self.assertIsNotNone(deleted_course.deleted_at)
        with self.assertRaises(Course.DoesNotExist):
            Course.objects.get(pk=target_course_pk)

    def test_delete_course_instructor_does_not_own_forbidden(self):
        """Instructors cannot delete courses owned by others."""
        headers = self._get_jwt_header(self.other_instructor_user)
        url = self.detail_url(self.course1_by_instructor.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_course_admin_can_delete_any(self):
        """Admins can delete any course."""
        headers = self._get_jwt_header(self.admin_user)
        target_course_pk = self.course1_by_instructor.pk
        url = self.detail_url(target_course_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        deleted_course = Course.all_objects.get(pk=target_course_pk)
        self.assertTrue(deleted_course.is_deleted)

    # === Soft Delete Custom Action Permissions ===
    def test_restore_course_student_forbidden(self):
        """Students cannot restore courses."""
        self.course3_to_delete.soft_delete()
        headers = self._get_jwt_header(self.student_user)
        url = self.restore_url(self.course3_to_delete.pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restore_course_instructor_forbidden(self):
        """Instructors cannot restore courses (as per MVP)."""
        self.course3_to_delete.soft_delete()
        headers = self._get_jwt_header(self.instructor_user)
        url = self.restore_url(self.course3_to_delete.pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restore_course_admin_success(self):
        """Admins can restore courses."""
        target_pk = self.course3_to_delete.pk
        self.course3_to_delete.soft_delete()
        self.assertTrue(Course.all_objects.get(pk=target_pk).is_deleted)
        headers = self._get_jwt_header(self.admin_user)
        url = self.restore_url(target_pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        restored_course = Course.objects.get(pk=target_pk)
        self.assertFalse(restored_course.is_deleted)
        self.assertIsNone(restored_course.deleted_at)

    def test_restore_non_deleted_course_admin_not_found(self):
        """Admin cannot 'restore' a course that isn't soft-deleted."""
        headers = self._get_jwt_header(self.admin_user)
        url = self.restore_url(self.course1_by_instructor.pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_list_student_forbidden(self):
        """Students cannot list deleted courses."""
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.deleted_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_list_instructor_forbidden(self):
        """Instructors cannot list deleted courses (as per MVP)."""
        headers = self._get_jwt_header(self.instructor_user)
        response = self.client.get(self.deleted_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_list_admin_success(self):
        """Admins can list deleted courses."""
        deleted_pk1 = self.course1_by_instructor.pk
        deleted_pk3 = self.course3_to_delete.pk
        self.course1_by_instructor.soft_delete()
        self.course3_to_delete.soft_delete()
        active_pk = self.course2_by_admin_as_instructor.pk

        headers = self._get_jwt_header(self.admin_user)
        response = self.client.get(self.deleted_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(deleted_pk1, result_ids)
        self.assertIn(deleted_pk3, result_ids)
        self.assertNotIn(active_pk, result_ids)

    # === File Upload Tests ===
    def test_create_course_with_image_instructor(self):
        """Instructors can create courses with image uploads."""
        self.maxDiff = None  # Show full diff on assertion failure
        headers = self._get_jwt_header(self.instructor_user)

        # Use context manager and ensure the file object is passed correctly
        temp_image_file = None
        try:
            # Create a temporary file object that persists
            temp_image_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            # Create the image content and save it to the file's path
            img = Image.new("RGB", (60, 30), color="red")
            img.save(temp_image_file.name, format="JPEG")
            temp_image_file.seek(0)  # Go back to the start of the file

            data = {
                "title": "Course With Image Upload Test",
                "description": "Testing image upload via test client.",
                "price": "33.00",
                "image": temp_image_file,  # Pass the file object
            }
            # Use format='multipart' explicitly if needed, though client often infers it
            response = self.client.post(
                self.list_create_url, data, format="multipart", **headers
            )

        finally:
            # Ensure the temporary file is closed and deleted
            if temp_image_file:
                temp_image_file.close()
                import os

                if os.path.exists(temp_image_file.name):
                    os.unlink(temp_image_file.name)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, f"API Error: {response.data}"
        )
        self.assertIn("image", response.data)
        self.assertIsNotNone(
            response.data["image"], "Image URL should not be null in the response"
        )
        self.assertIsInstance(response.data["image"], str)
        self.assertTrue(
            len(response.data["image"]) > 0, "Image URL should not be empty"
        )
        self.assertIn(
            "/media/course_images/",
            response.data["image"],
            "Image URL should contain the media path",
        )

        # Verify DB object has the image saved
        try:
            new_course = Course.objects.get(pk=response.data["id"])
            self.assertTrue(
                new_course.image,
                "Course object in DB should have an image file associated",
            )
            self.assertTrue(
                len(new_course.image.name) > 0, "Image field name should not be empty"
            )
            self.assertTrue(
                new_course.image.name.startswith("course_images/"),
                f"Image name '{new_course.image.name}' does not start with 'course_images/'",
            )
            # Optionally check if the file actually exists in storage (more complex)
            # from django.core.files.storage import default_storage
            # self.assertTrue(default_storage.exists(new_course.image.name))
        except Course.DoesNotExist:
            self.fail("Course was not created in the database.")

        self.assertEqual(new_course.instructor, self.instructor_user)

    def test_update_course_remove_image_owner_instructor(self):
        """Owner instructor can remove an image by sending null."""
        headers_instructor = self._get_jwt_header(self.instructor_user)
        temp_image_file = None
        try:
            temp_image_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            image_file_upload = get_temporary_image_file(temp_image_file)
            add_image_url = self.detail_url(self.course1_by_instructor.pk)
            # Use format='multipart' for PATCH with file upload
            add_image_response = self.client.patch(
                add_image_url,
                {"image": image_file_upload},
                format="multipart",
                **headers_instructor,
            )
            # Close the file object after the request
            image_file_upload.close()
        finally:
            if temp_image_file:
                import os

                if os.path.exists(temp_image_file.name):
                    os.unlink(temp_image_file.name)

        self.assertEqual(add_image_response.status_code, status.HTTP_200_OK)
        self.course1_by_instructor.refresh_from_db()
        self.assertTrue(
            self.course1_by_instructor.image, "Image should have been added"
        )

        # Now remove image using JSON payload with null
        remove_image_data = {"image": None}
        remove_image_response = self.client.patch(
            add_image_url, remove_image_data, format="json", **headers_instructor
        )
        self.assertEqual(
            remove_image_response.status_code,
            status.HTTP_200_OK,
            remove_image_response.data,
        )
        self.assertIsNone(
            remove_image_response.data["image"], "Image should be null in response"
        )
        self.course1_by_instructor.refresh_from_db()
        self.assertFalse(
            self.course1_by_instructor.image, "Image should be removed from DB"
        )

    def test_update_course_remove_image_admin(self):
        """Admin can remove an image from any course by sending null."""
        # Add image as instructor first
        headers_instructor = self._get_jwt_header(self.instructor_user)
        temp_image_file = None
        try:
            temp_image_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            image_file_upload = get_temporary_image_file(temp_image_file)
            add_image_response = self.client.patch(
                self.detail_url(self.course1_by_instructor.pk),
                {"image": image_file_upload},
                format="multipart",
                **headers_instructor,
            )
            image_file_upload.close()
        finally:
            if temp_image_file:
                import os

                if os.path.exists(temp_image_file.name):
                    os.unlink(temp_image_file.name)
        self.assertEqual(add_image_response.status_code, status.HTTP_200_OK)
        self.course1_by_instructor.refresh_from_db()
        self.assertTrue(
            self.course1_by_instructor.image,
            "Image should have been added by instructor",
        )

        # Now admin removes it
        headers_admin = self._get_jwt_header(self.admin_user)
        remove_image_data = {"image": None}
        remove_image_response = self.client.patch(
            self.detail_url(self.course1_by_instructor.pk),
            remove_image_data,
            format="json",
            **headers_admin,
        )
        self.assertEqual(remove_image_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            remove_image_response.data["image"],
            "Image should be null in response after admin removal",
        )
        self.course1_by_instructor.refresh_from_db()
        self.assertFalse(
            self.course1_by_instructor.image, "Image should be removed from DB by admin"
        )
