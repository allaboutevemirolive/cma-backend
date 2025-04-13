# src/apps/enrollments/apps.py
from django.apps import AppConfig

class EnrollmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # IMPORTANT: Use the nested path name
    name = 'apps.enrollments'
    verbose_name = "Enrollments"
