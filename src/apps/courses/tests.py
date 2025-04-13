# src/apps/courses/tests.py

import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone  # For checking deleted_at
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Course  # Import the Course model


# Helper function to create a dummy image file (remains the same)
def get_temporary_image_file(temp_file=None):
    img = Image.new("RGB", (10, 10), color="red")
    temp_file = temp_file or tempfile.NamedTemporaryFile(suffix=".jpg")
    img.save(temp_file, format="JPEG")
    temp_file.seek(0)
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
        # User profiles should be created automatically by signals if profiles app is set up

        # Create 'Instructors' group and add instructor user
        # Assumes IsAdminOrInstructor permission checks this group or is_staff
        cls.instructors_group, created = Group.objects.get_or_create(name="Instructors")
        cls.instructor_user.groups.add(cls.instructors_group)
        cls.instructor_user.save()  # Save user after adding group

        # Create some initial courses using the ForeignKey for instructor
        cls.course1 = Course.objects.create(
            title="Test Course 1 by Instructor",
            description="Desc 1",
            price="10.00",
            instructor=cls.instructor_user,  # Assign User object
            status=Course.Status.ACTIVE,
        )
        # Create a second course with a different instructor for filtering tests
        cls.course2 = Course.objects.create(
            title="Test Course 2 by Admin",
            description="Desc 2",
            price="20.00",
            instructor=cls.admin_user,  # Assign admin user
            status=Course.Status.INACTIVE,
        )
        # Create a third course to test soft delete visibility
        cls.course_to_delete = Course.objects.create(
            title="Course to Delete",
            description="Will be soft-deleted",
            price="5.00",
            instructor=cls.instructor_user,
            status=Course.Status.ACTIVE,
        )

        # URLs
        cls.list_create_url = reverse("course-list")
        cls.detail_url = lambda pk: reverse("course-detail", kwargs={"pk": pk})
        # URLs for custom actions (ensure these match url_path in views.py)
        cls.restore_url = lambda pk: reverse("course-restore", kwargs={"pk": pk})
        cls.deleted_list_url = reverse("course-deleted-list")

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
            "instructor_id": 1,  # Need instructor_id in payload
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Permission Tests (RBAC) ---
    def test_list_courses_student(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.list_create_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Default list shows non-deleted courses (3 initial courses)
        self.assertEqual(response.data["count"], 3)

    def test_create_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        data = {
            "title": "Student Course",
            "description": "Should Fail",
            "price": "5.00",
            "instructor_id": self.student_user.id,  # Send ID
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_instructor(self):
        headers = self._get_jwt_header(self.instructor_user)
        data = {
            "title": "Instructor Course",
            "description": "Should Pass",
            "price": "50.00",
            "instructor_id": self.instructor_user.id,  # Send instructor ID
            "status": Course.Status.DRAFT,  # Test setting status
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Course.objects.count(), 4)  # 3 initial + 1 new
        new_course = Course.objects.get(pk=response.data["id"])
        self.assertEqual(new_course.instructor, self.instructor_user)
        self.assertEqual(new_course.status, Course.Status.DRAFT)

    def test_create_course_admin(self):
        headers = self._get_jwt_header(self.admin_user)
        data = {
            "title": "Admin Course",
            "description": "Should Pass",
            "price": "100.00",
            "instructor_id": self.instructor_user.id,  # Admin assigning another instructor
        }
        response = self.client.post(
            self.list_create_url, data, format="json", **headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # Count depends on which tests run before, check based on current context
        self.assertEqual(Course.objects.filter(title="Admin Course").count(), 1)
        new_course = Course.objects.get(title="Admin Course")
        self.assertEqual(new_course.instructor, self.instructor_user)

    def test_update_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        data = {"title": "Updated Title Fail"}
        url = self.detail_url(self.course1.pk)
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_instructor_owns(self):
        headers = self._get_jwt_header(self.instructor_user)
        new_title = "Updated By Instructor"
        data = {"title": new_title, "price": "12.00"}
        url = self.detail_url(self.course1.pk)  # course1 owned by instructor_user
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, new_title)
        self.assertEqual(self.course1.price, 12.00)

    def test_update_course_instructor_does_not_own(self):
        # Instructors should typically only update their own courses unless admin
        # Adjust IsAdminOrInstructor permission if needed
        headers = self._get_jwt_header(self.instructor_user)
        data = {"title": "Update Fail"}
        url = self.detail_url(self.course2.pk)  # course2 owned by admin_user
        response = self.client.patch(url, data, format="json", **headers)
        # Assuming instructors can only modify their own courses
        # If IsAdminOrInstructor allows any instructor to modify any course, change this to 200 OK
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )  # Or 404 if not found by view's queryset

    def test_update_course_admin(self):
        headers = self._get_jwt_header(self.admin_user)
        new_status = Course.Status.INACTIVE
        data = {
            "status": new_status,
            "instructor_id": self.admin_user.id,
        }  # Change status and instructor
        url = self.detail_url(self.course1.pk)  # Update course1
        response = self.client.patch(url, data, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.status, new_status)
        self.assertEqual(self.course1.instructor, self.admin_user)

    def test_delete_course_student(self):
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.course_to_delete.pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_course_instructor_owns(self):
        headers = self._get_jwt_header(self.instructor_user)
        target_course_pk = self.course_to_delete.pk
        url = self.detail_url(target_course_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete using all_objects manager
        deleted_course = Course.all_objects.get(pk=target_course_pk)
        self.assertTrue(deleted_course.is_deleted)
        self.assertIsNotNone(deleted_course.deleted_at)

        # Verify it's not in default queryset
        with self.assertRaises(Course.DoesNotExist):
            Course.objects.get(pk=target_course_pk)

    def test_delete_course_admin(self):
        headers = self._get_jwt_header(self.admin_user)
        # Use course1 for admin delete test
        target_course_pk = self.course1.pk
        url = self.detail_url(target_course_pk)
        response = self.client.delete(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete using all_objects manager
        deleted_course = Course.all_objects.get(pk=target_course_pk)
        self.assertTrue(deleted_course.is_deleted)
        self.assertIsNotNone(deleted_course.deleted_at)

        # Verify it's not in default queryset
        with self.assertRaises(Course.DoesNotExist):
            Course.objects.get(pk=target_course_pk)

    # --- CRUD Tests ---
    def test_retrieve_course_detail(self):
        headers = self._get_jwt_header(
            self.student_user
        )  # Any authenticated user can retrieve
        url = self.detail_url(self.course1.pk)
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.course1.title)
        # Check for nested instructor data
        self.assertIn("instructor", response.data)
        self.assertIsNotNone(response.data["instructor"])
        self.assertEqual(response.data["instructor"]["id"], self.instructor_user.id)
        self.assertEqual(
            response.data["instructor"]["username"], self.instructor_user.username
        )

    def test_retrieve_non_existent_course(self):
        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(9999)  # Non-existent PK
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_soft_deleted_course(self):
        # Soft delete a course first
        self.course_to_delete.soft_delete()

        headers = self._get_jwt_header(self.student_user)
        url = self.detail_url(self.course_to_delete.pk)
        response = self.client.get(url, **headers)
        # Default manager/viewset queryset excludes soft-deleted items
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Filtering/Pagination/Ordering Tests ---
    def test_filter_course_by_status(self):
        headers = self._get_jwt_header(self.student_user)
        # Filter for active (course1, course_to_delete initially)
        response_active = self.client.get(
            f"{self.list_create_url}?status=active", **headers
        )
        self.assertEqual(response_active.status_code, status.HTTP_200_OK)
        self.assertEqual(response_active.data["count"], 2)
        active_ids = {item["id"] for item in response_active.data["results"]}
        self.assertIn(self.course1.id, active_ids)
        self.assertIn(self.course_to_delete.id, active_ids)

        # Filter for inactive (course2)
        response_inactive = self.client.get(
            f"{self.list_create_url}?status=inactive", **headers
        )
        self.assertEqual(response_inactive.status_code, status.HTTP_200_OK)
        self.assertEqual(response_inactive.data["count"], 1)
        self.assertEqual(response_inactive.data["results"][0]["id"], self.course2.id)

    def test_filter_course_by_instructor_id(self):
        headers = self._get_jwt_header(self.student_user)
        # Filter by instructor_user (course1, course_to_delete)
        response_inst = self.client.get(
            f"{self.list_create_url}?instructor_id={self.instructor_user.id}", **headers
        )
        self.assertEqual(response_inst.status_code, status.HTTP_200_OK)
        self.assertEqual(response_inst.data["count"], 2)
        inst_ids = {item["id"] for item in response_inst.data["results"]}
        self.assertIn(self.course1.id, inst_ids)
        self.assertIn(self.course_to_delete.id, inst_ids)

        # Filter by admin_user (course2)
        response_admin = self.client.get(
            f"{self.list_create_url}?instructor_id={self.admin_user.id}", **headers
        )
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(response_admin.data["count"], 1)
        self.assertEqual(response_admin.data["results"][0]["id"], self.course2.id)

    def test_search_course_by_title(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(f"{self.list_create_url}?search=Course 1", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course1.id)

    def test_search_course_by_instructor_username(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(
            f"{self.list_create_url}?search=testadmin", **headers
        )  # Search for course2 instructor
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.course2.id)

    def test_order_course_by_price_descending(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(f"{self.list_create_url}?ordering=-price", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["count"], 1)
        prices = [float(item["price"]) for item in response.data["results"]]
        # Check if prices are sorted in descending order
        self.assertEqual(prices, sorted(prices, reverse=True))

    # --- File Upload Test ---
    def test_create_course_with_image(self):
        headers = self._get_jwt_header(self.admin_user)
        image_file = get_temporary_image_file()
        data = {
            "title": "Course With Image",
            "description": "Testing upload",
            "price": "30.00",
            "instructor_id": self.admin_user.id,  # Need instructor_id
            "image": image_file,
        }
        response = self.client.post(
            self.list_create_url, data, **headers
        )  # Use default multipart
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn("image", response.data)
        self.assertIsNotNone(response.data["image"])

        image_url = response.data["image"]
        self.assertTrue(
            image_url.startswith("/media/course_images/")
        )  # Or full URL depending on settings
        # Check if the course object in DB has the image path set
        new_course = Course.objects.get(pk=response.data["id"])
        self.assertTrue(new_course.image.name.startswith("course_images/"))

    def test_update_course_remove_image(self):
        # First, create a course with an image
        headers_admin = self._get_jwt_header(self.admin_user)
        image_file = get_temporary_image_file()
        create_data = {
            "title": "Course Image Removal Test",
            "description": "Desc",
            "price": "5.00",
            "instructor_id": self.admin_user.id,
            "image": image_file,
        }
        create_response = self.client.post(
            self.list_create_url, create_data, **headers_admin
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        course_id = create_response.data["id"]
        course = Course.objects.get(pk=course_id)
        self.assertTrue(course.image.name)  # Ensure image exists initially

        # Now, update the course sending null for the image
        update_data = {"image": None}
        update_url = self.detail_url(course_id)
        update_response = self.client.patch(
            update_url, update_data, format="json", **headers_admin
        )  # Use json for null

        self.assertEqual(
            update_response.status_code, status.HTTP_200_OK, update_response.data
        )
        self.assertIn("image", update_response.data)
        self.assertIsNone(
            update_response.data["image"]
        )  # Check API response shows null

        # Verify in DB
        course.refresh_from_db()
        self.assertFalse(course.image)  # Image field should be empty/null

    # --- Soft Delete Custom Action Tests ---

    def test_restore_course_permission_denied(self):
        # Soft delete course1 first
        self.course1.soft_delete()
        self.assertTrue(Course.all_objects.get(pk=self.course1.pk).is_deleted)

        headers = self._get_jwt_header(self.student_user)  # Student cannot restore
        url = self.restore_url(self.course1.pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restore_course_success(self):
        # Soft delete course1 first
        self.course1.soft_delete()
        self.assertTrue(Course.all_objects.get(pk=self.course1.pk).is_deleted)

        headers = self._get_jwt_header(self.admin_user)  # Admin can restore
        url = self.restore_url(self.course1.pk)
        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify restored course
        restored_course = Course.objects.get(
            pk=self.course1.pk
        )  # Should now be in default manager
        self.assertFalse(restored_course.is_deleted)
        self.assertIsNone(restored_course.deleted_at)
        self.assertEqual(response.data["id"], restored_course.id)

    def test_restore_non_deleted_course(self):
        headers = self._get_jwt_header(self.admin_user)
        url = self.restore_url(self.course2.pk)  # course2 was never deleted
        response = self.client.post(url, **headers)
        # Should be 404 because the view looks for is_deleted=True
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_list_permission_denied(self):
        headers = self._get_jwt_header(self.student_user)
        response = self.client.get(self.deleted_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleted_list_success(self):
        # Delete course1 and course_to_delete
        deleted_pk1 = self.course1.pk
        deleted_pk2 = self.course_to_delete.pk
        self.course1.soft_delete()
        self.course_to_delete.soft_delete()

        # course2 remains active
        active_pk = self.course2.pk

        headers = self._get_jwt_header(self.admin_user)  # Admin can view deleted list
        response = self.client.get(self.deleted_list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response contains only the deleted items
        self.assertEqual(response.data["count"], 2)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(deleted_pk1, result_ids)
        self.assertIn(deleted_pk2, result_ids)
        self.assertNotIn(active_pk, result_ids)
