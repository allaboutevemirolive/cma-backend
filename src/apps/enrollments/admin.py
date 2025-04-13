# src/apps/enrollments/admin.py
from django.contrib import admin
from .models import Enrollment

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrollment_date', 'is_deleted')
    list_filter = ('status', 'course', 'is_deleted')
    search_fields = ('student__username', 'course__title')
    # actions = ['restore_enrollments'] # Optional: Add admin action to restore

    def get_queryset(self, request):
         return Enrollment.all_objects.all() # Show all in admin

    # Optional: Restore action
    # @admin.action(description='Restore selected enrollments')
    # def restore_enrollments(self, request, queryset):
    #     queryset.update(is_deleted=False, deleted_at=None)
