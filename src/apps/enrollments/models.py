# src/apps/enrollments/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.courses.models import Course


class EnrollmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_including_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # If user deleted, remove enrollment
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,  # If course deleted, remove enrollment
        related_name="enrollments",
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft Delete (Recommended)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = EnrollmentManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = (
            "student",
            "course",
            "is_deleted",
        )  # Allow re-enrollment if soft-deleted
        ordering = ["-enrollment_date"]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save()

    # Override delete
    def delete(self, using=None, keep_parents=False):
        self.soft_delete()
