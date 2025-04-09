# backend/courses/models.py

from django.db import models
from django.utils import timezone

# --- Custom Manager for Soft Delete ---
class CourseManager(models.Manager):
    def get_queryset(self):
        # Default queryset excludes soft-deleted items
        return super().get_queryset().filter(is_deleted=False)

    def all_objects(self):
        # Method to get all items, including soft-deleted ones
        return super().get_queryset()

    def deleted_objects(self):
         # Method to get only soft-deleted items
        return super().get_queryset().filter(is_deleted=True)

# --- Course Model ---
class Course(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    instructor_id = models.IntegerField(
        help_text="Using IntegerField for simplicity. Consider ForeignKey to a User/Instructor model."
    ) # In a real app, this should likely be a ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    image_url = models.URLField(max_length=500, blank=True, null=True)

    is_deleted = models.BooleanField(default=False) # For soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True) # Record deletion time

    # Managers
    objects = CourseManager()  # Default manager (filters out deleted)
    all_objects = models.Manager() # Manager to access all objects including deleted

    def __str__(self):
        return self.title

    def soft_delete(self):
        """Marks the instance as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restores a soft-deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    # Override the default delete() method to implement soft delete
    def delete(self, using=None, keep_parents=False):
        self.soft_delete()

    class Meta:
        ordering = ['-created_at'] # Default ordering
        verbose_name = "Course"
        verbose_name_plural = "Courses"
