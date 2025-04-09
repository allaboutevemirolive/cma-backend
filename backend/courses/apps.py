# backend/courses/apps.py

from django.apps import AppConfig

class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField' # Optional, but good practice
    name = 'courses' # This should match your app's directory name
