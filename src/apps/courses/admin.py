# backend/courses/admin.py
from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'status', 'created_at', 'is_deleted')
    list_filter = ('status', 'is_deleted', 'instructor') # Filter by instructor object
    search_fields = ('title', 'description', 'instructor__username') # Search by username
    # To see all objects including soft-deleted ones in admin:
    def get_queryset(self, request):
         return Course.all_objects.all() # Use the manager that shows all objects
