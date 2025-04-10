# src/config/asgi.py 

import os
from django.core.asgi import get_asgi_application

# Update path to settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
# Add websocket/channel routing here if needed in the future
