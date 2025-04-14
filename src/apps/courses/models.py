# src/apps/courses/models.py

from django.db import models
from django.utils import timezone
from django.conf import settings # To link instructor to settings.AUTH_USER_MODEL
# from django.core.validators import MinValueValidator # Optional: For price validation

# --- Custom Manager for Soft Delete ---
class CourseManager(models.Manager):
    """
    Custom manager for the Course model that handles soft deletion.
    The default manager ('objects') excludes soft-deleted items.
    Provides methods to access all items or only deleted items.
    """
    def get_queryset(self):
        """
        Override the default queryset to exclude items marked as deleted.
        This manager will be assigned to 'objects'.
        """
        return super().get_queryset().filter(is_deleted=False)

    def all_including_deleted(self):
        """
        Returns a queryset containing all course objects, including those
        marked as deleted. Useful for admin or recovery operations.
        """
        return super().get_queryset()

    def deleted_only(self):
         """
         Returns a queryset containing only course objects that have been
         marked as deleted.
         """
         return super().get_queryset().filter(is_deleted=True)


# --- Course Model ---
class Course(models.Model):
    """
    Represents a course offered on the learning platform.
    Includes fields for title, description, price, instructor, status,
    and an optional image. Implements soft deletion.
    """
    class Status(models.TextChoices):
        """Enum-like choices for the course status."""
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        DRAFT = 'draft', 'Draft' # Added Draft status

    # --- Core Fields ---
    title = models.CharField(
        max_length=255,
        blank=False, # Title is required
        null=False,
        help_text="The title of the course."
    )
    description = models.TextField(
        blank=False, # Description is required
        null=False,
        help_text="A detailed description of the course content."
    )
    price = models.DecimalField(
        max_digits=10,      # Maximum number of digits including decimal places
        decimal_places=2,   # Number of decimal places to store
        blank=False,        # Price is required
        null=False,
        help_text="The price of the course.",
        # validators=[MinValueValidator(0.00)] # Optional: Ensure price is not negative
    )
    # --- Instructor ForeignKey ---
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Or PROTECT if instructor must exist
        null=True,                 # Allow null temporarily or if instructor deleted
        blank=False,               # Instructor is logically required, but allow null in DB via SET_NULL
        related_name='courses_taught', # Access courses from user: user.courses_taught.all()
        help_text="The user designated as the instructor for this course."
        # Optional: Limit choices in admin/forms
        # limit_choices_to={'profile__role': 'instructor'} # Assumes Profile model exists
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT, # Default to Draft status
        help_text="The current status of the course (e.g., Draft, Active, Inactive)."
    )
    image = models.ImageField(
        upload_to='course_images/', # Files will be saved to MEDIA_ROOT/course_images/
        blank=True,     # Image is optional
        null=True,      # Allow null in the database
        help_text="An optional image representing the course."
    )

    # --- Soft Delete Fields ---
    is_deleted = models.BooleanField(
        default=False,
        db_index=True, # Index for faster filtering of non-deleted items
        help_text="Flag indicating if the course has been soft-deleted."
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when the course was soft-deleted."
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(
        auto_now_add=True, # Automatically set when the object is first created
        editable=False,    # Prevent editing in forms/admin
        help_text="Timestamp when the course was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,     # Automatically set every time the object is saved
        editable=False,    # Prevent editing in forms/admin
        help_text="Timestamp when the course was last updated."
    )

    # --- Managers ---
    # Default manager: filters out soft-deleted items
    objects = CourseManager()
    # Secondary manager: provides access to *all* items, including soft-deleted ones
    all_objects = models.Manager() # Standard Django manager

    # --- Meta Options ---
    class Meta:
        ordering = ['-created_at'] # Default ordering for querysets (newest first)
        verbose_name = "Course"        # Singular name used in Django admin
        verbose_name_plural = "Courses"  # Plural name used in Django admin
        indexes = [ # Optional but good: Add database indexes for frequently queried fields
            models.Index(fields=['status']),
            models.Index(fields=['instructor']),
            models.Index(fields=['is_deleted', 'deleted_at']), # Composite index for soft delete
        ]

    # --- Instance Methods ---
    def __str__(self):
        """String representation of the Course model, used in admin and debugging."""
        instructor_name = self.instructor.username if self.instructor else "No Instructor Assigned"
        return f"{self.title} (by {instructor_name})"

    def soft_delete(self):
        """Marks the instance as deleted by setting the flag and timestamp."""
        if not self.is_deleted: # Prevent multiple updates if already deleted
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at']) # Optimize save

    def restore(self):
        """Restores a soft-deleted instance by unsetting the flag and timestamp."""
        if self.is_deleted: # Only restore if currently deleted
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at']) # Optimize save

    # Override the default delete() method to enforce soft delete
    def delete(self, using=None, keep_parents=False):
        """
        Overrides the default Django delete behavior to perform a soft delete
        instead of removing the record from the database.
        """
        self.soft_delete()
        # Note: We don't call super().delete() here, as that would perform a hard delete.

    # def is_active_for_enrollment(self):
    #    """Checks if the course is active and not deleted."""
    #    return self.status == self.Status.ACTIVE and not self.is_deleted

    # def get_enrollment_count(self):
    #    """Returns the number of active enrollments."""
    #    # Assumes Enrollment model has a related_name='enrollments' on course FK
    #    return self.enrollments.filter(status='active', is_deleted=False).count()
