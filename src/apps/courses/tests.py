# backend/courses/tests.py

from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken  # To generate tokens for tests
from .models import Course

# For file uploads in tests:
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


# Helper function to create a dummy image file
def get_temporary_image_file(temp_file=None):
    img = Image.new("RGB", (10, 10), color="red")  # Create a small red image
    temp_file = temp_file or tempfile.NamedTemporaryFile(suffix=".jpg")
    img.save(temp_file, format="JPEG")
    temp_file.seek(0)  # Important: move back to the beginning of the file
    return SimpleUploadedFile(
        temp_file.name, temp_file.read(), content_type="image/jpeg"
    )


class CourseApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users with different roles
        cls.admin_user = User.objects.create_superuser(
            username="testadmin", password="password123", email="admin@test.com"
        )
        cls.instructor_user = User.objects.create_user(
            username="testinstructor",
            password="password123",
            email="instructor@test.com",
        )
        cls.student_user = User.objects.create_user(
            username="teststudent", password="password123", email="student@test.com"
        )

        # Create 'Instructors' group and add instructor user
        cls.instructors_group = Group.objects.create(name="Instructors")
        cls.instructor_user.groups.add(cls.instructors_group)

        # Create some initial courses
        cls.course1 = Course.objects.create(
            title="Test Course 1",
            description="Desc 1",
            price="10.00",
            instructor_id=cls.instructor_user.id,
            status="active",
        )
        cls.course2 = Course.objects.create(
            title="Test Course 2",
            description="Desc 2",
            price="20.00",
            instructor_id=99,
            status="inactive",  # Different instructor ID
        )

        # URLs
        cls.list_create_url = reverse(
            "course-list"
        )  # DRF default name is '<basename>-list'
        cls.detail_url = lambda pk: reverse(
            "course-detail", kwargs={"pk": pk}
        )  # '<basename>-detail'

    def _get_jwt_header(self, user):
        # Helper to get JWT token header for a user
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    # --- Authentication Tests ---
    def test_list_courses_unauthenticated(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_course_unauthenticated(self):
        data = {
            "title": "Fail",
            "description": "Fail",
            "price": "5.00",
            "instructor_id": 1,
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Permission Tests (RBAC) ---
    def test_list_courses_student(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # By default, list shows non-deleted courses
        self.assertEqual(response.data["count"], 2)

    def test_create_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        data = {
            "title": "Student Course",
            "description": "Should Fail",
            "price": "5.00",
            "instructor_id": self.student_user.id,
        }
        response = self.client.post(self.list_create_url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_instructor(self):
        headers = self._get_jwt_header(self.instructor_user)
        data = {
            "title": "Instructor Course",
            "description": "Should Pass",
            "price": "50.00",
            "instructor_id": self.instructor_user.id,
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )  # Use format='json'
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 3)  # 2 initial + 1 new

    def test_create_course_admin(self):
        headers = self._get_jwt_header(self.admin_user)
        data = {
            "title": "Admin Course",
            "description": "Should Pass",
            "price": "100.00",
            "instructor_id": self.admin_user.id,
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Course.objects.count(), 3
        )  # 2 initial + 1 new (runs independently from instructor test)

    def test_update_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        data = {"title": "Updated Title Fail"}
        url = self.detail_url(self.course1.pk)
        response = self.client.patch(
            url, data, format="json", **headers
        )  # Use PATCH for partial update
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_instructor(self):
        headers = self._get_jwt_header(self.instructor_user)
        new_title = "Updated By Instructor"
        data = {"title": new_title}
        url = self.detail_url(self.course1.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, new_title)

    def test_delete_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.course1.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_course_instructor(self):
        headers = self._get_jwt_header(self.instructor_user)
        url = self.detail_url(self.course1.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify soft delete
        self.assertTrue(Course.all_objects.get(pk=self.course1.pk).is_deleted)
        # Check it's not in default queryset
        with self.assertRaises(Course.DoesNotExist):
            Course.objects.get(pk=self.course1.pk)

    # --- CRUD Tests ---
    def test_retrieve_course_detail(self):
        headers = self._get_jwt_header(
            self.student_user
        )  # Any authenticated user can retrieve
        url = self.detail_url(self.course1.pk)
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.course1.title)

    def test_retrieve_non_existent_course(self):
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(999)  # Non-existent PK
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Filtering/Pagination Tests ---
    def test_filter_course_by_status(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.list_create_url + "?status=active", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course1.id)

        response = self.client.get(self.list_create_url + "?status=inactive", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course2.id)

    def test_filter_course_by_instructor_id(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(
            f"{self.list_create_url}?instructor_id={self.instructor_user.id}", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course1.id)

        response = self.client.get(
            f"{self.list_create_url}?instructor_id=99", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course2.id)

    # --- File Upload Test ---
    def test_create_course_with_image(self):
        headers = self._get_jwt_header(self.admin_user)  # Admin can create
        image_file = get_temporary_image_file()
        data = {
            "title": "Course With Image",
            "description": "Testing upload",
            "price": "30.00",
            "instructor_id": self.admin_user.id,
            "image": image_file,
        }
        # When sending files, don't set format='json'
        response = self.client.post(
            self.list_create_url, data, **headers
        )  # Use default multipart

        # --- Start Modifications ---
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("image", response.data) # Ensure the key exists
        self.assertIsNotNone(response.data["image"]) # Ensure the value isn't null

        image_url = response.data["image"] # Get the actual URL from the response
        expected_path_segment = "/media/course_images/" # The part we expect regardless of domain

        # Check if the expected path segment is *contained within* the returned URL
        self.assertIn(
            expected_path_segment,
            image_url,
            f"Image URL '{image_url}' does not contain expected path '{expected_path_segment}'"
        )

        # Optional: Check if it ends with the correct extension (more specific)
        # file_name = image_url.split('/')[-1] # Get the filename part
        # self.assertTrue(file_name.endswith('.jpg'), f"Filename '{file_name}' doesn't end with .jpg")
        # --- End Modifications ---

        # Optional: Check if file exists on disk (more complex, involves settings and temp dirs)
        # from django.conf import settings
        # import os
        # # Note: Test runner usually uses a temporary MEDIA_ROOT
        # # This check might be fragile if MEDIA_ROOT handling changes.
        # file_path = os.path.join(settings.MEDIA_ROOT, 'course_images', os.path.basename(image_url))
        # self.assertTrue(os.path.exists(file_path), f"File not found at calculated path: {file_path}")
