# backend/courses/admin.py
from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor_id', 'price', 'status', 'created_at', 'is_deleted')
    list_filter = ('status', 'is_deleted', 'instructor_id')
    search_fields = ('title', 'description')
    # To see all objects including soft-deleted ones in admin:
    def get_queryset(self, request):
         return Course.all_objects.all() # Use the manager that shows all objects
