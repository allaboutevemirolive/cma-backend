# src/apps/courses/apps.py

from django.apps import AppConfig

class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Update the name to reflect its location within 'apps'
    name = 'apps.courses'
    verbose_name = "Courses" # Optional: Nicer name for admin
