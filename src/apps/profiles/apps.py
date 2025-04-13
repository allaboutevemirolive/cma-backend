# src/apps/profiles/apps.py
from django.apps import AppConfig

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # IMPORTANT: Update the name to reflect the nested structure
    name = 'apps.profiles'
    verbose_name = "Profiles"
