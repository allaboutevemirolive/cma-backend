# src/apps/quizzes/apps.py
from django.apps import AppConfig

class QuizzesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.quizzes' # Use nested path name
    verbose_name = "Quizzes and Submissions"
