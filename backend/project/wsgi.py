# backend/project/wsgi.py

import os

from django.core.wsgi import get_wsgi_application

# Make sure 'project.settings' matches your Django project's settings file location
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()
