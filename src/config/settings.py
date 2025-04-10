# src/config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta

# --- Base Directories ---
# BASE_DIR points to the 'src/' directory where manage.py lives.
BASE_DIR = Path(__file__).resolve().parent.parent
# PROJECT_ROOT points to the directory containing 'src/', 'Dockerfile', 'requirements.txt', etc.
PROJECT_ROOT = BASE_DIR.parent

# --- Environment Variables ---
# Load environment variables from .env file located in the PROJECT_ROOT
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# --- Security Settings ---
# SECURITY WARNING: keep the secret key used in production secret!
# Set this in your .env file.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-fallback-change-me!')

# SECURITY WARNING: don't run with debug turned on in production!
# Set DEBUG=False in your .env file for production.
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Define allowed hosts via .env, defaulting to localhost for development.
# Example .env: ALLOWED_HOSTS=yourdomain.com,127.0.0.1
ALLOWED_HOSTS_STRING = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []
# In Docker setups, you might need to add the service name or '0.0.0.0' if accessed internally.
# ALLOWED_HOSTS.append('web') # Example if service name is 'web'


# --- Application Definition ---
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Handles static files

    # Third-Party Apps
    'rest_framework',                # Django REST Framework core
    'rest_framework_simplejwt',      # JWT token authentication
    # 'rest_framework_simplejwt.token_blacklist', # Optional: for token blacklisting
    'django_filters',                # Filtering capabilities for DRF views
    'drf_yasg',                      # OpenAPI/Swagger documentation generation

    # Your Project's Apps (Update paths relative to src/)
    'apps.courses.apps.CoursesConfig', # Correct path to the app config
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Manages sessions
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',           # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # User authentication
    'django.contrib.messages.middleware.MessageMiddleware', # Message framework
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking protection
]

# --- Root URLConf ---
# Points to the main urls.py file within the 'config' directory.
ROOT_URLCONF = 'config.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Optional: Add project-level templates directory if needed: [BASE_DIR / 'templates']
        'DIRS': [],
        'APP_DIRS': True, # Look for templates in app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- WSGI & ASGI ---
# Entry points for web servers. Use the paths relative to 'src'.
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application' # Define even if not using Channels/ASGI server yet


# --- Database ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# Read database configuration from the DATABASE_URL environment variable.
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600, # Optional: connection pooling time
            ssl_require=os.getenv('DB_SSL_REQUIRE', 'False').lower() == 'true'
        )
    }
else:
    # Fallback to SQLite if DATABASE_URL is not set (for local dev without Docker, or initial setup).
    print("WARNING: DATABASE_URL environment variable not found. Falling back to SQLite database at project root.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            # Store the SQLite DB at the project root (outside 'src')
            'NAME': PROJECT_ROOT / 'db.sqlite3',
        }
    }


# --- Password Validation ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# --- Internationalization ---
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC' # Recommended to use UTC
USE_I18N = True   # Enable internationalization features
USE_TZ = True     # Enable timezone support for datetimes


# --- Static Files ---
# https://docs.djangoproject.com/en/4.2/howto/static-files/
# Files served directly by the web server in production (CSS, JS, app images).
STATIC_URL = '/static/'
# Directory where 'collectstatic' will gather static files for deployment.
# Should be outside 'src', typically at the project root.
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'
# Optional: Directories where Django will look for static files in addition to app 'static' directories.
# STATICFILES_DIRS = [ BASE_DIR / "static", ]


# --- Media Files ---
# https://docs.djangoproject.com/en/4.2/topics/files/
# User-uploaded files (e.g., course images).
MEDIA_URL = '/media/'
# Absolute path to the directory where media files are stored.
# Should be outside 'src', typically at the project root.
MEDIA_ROOT = PROJECT_ROOT / 'media'


# --- Default Primary Key Field Type ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Django REST Framework Settings ---
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication', # Keep commented unless needed for Browsable API login
    ),

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Default to requiring authentication
    ],

    # 'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema', # Default schema if not using drf-yasg view
}


# --- Simple JWT Settings ---
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Example: 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),   # Example: 1 day
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False, # Requires blacklist app enabled
    "UPDATE_LAST_LOGIN": True,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY, # Use Django's SECRET_KEY
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,

    "AUTH_HEADER_TYPES": ("Bearer",), # Standard "Bearer <token>" header
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}


# --- drf-yasg (Swagger/OpenAPI) Settings ---
# https://drf-yasg.readthedocs.io/en/stable/settings.html
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': { # Scheme name
            'type': 'apiKey',
            'name': 'Authorization', # Header name
            'in': 'header',
            'description': 'JWT Token (Prefix with "Bearer "). Example: "Bearer eyJ..."'
        }
    },
    'USE_SESSION_AUTH': False, # Use token auth for Swagger UI, not session
    'JSON_EDITOR': True,
    'SHOW_REQUEST_HEADERS': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'patch', 'delete'],
}
# URLs needed if using Django login in Swagger UI
LOGIN_URL = '/admin/login/'
LOGOUT_URL = '/admin/logout/'

# --- Logging (Optional - Example Configuration) ---
# LOGGING = { ... }
# --- Logging (Optional but Recommended) ---
# Configure how application logs are handled.
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple', # Use 'verbose' for more detail
#         },
#         # Add file handlers for production logging if needed
#         # 'file': {
#         #     'level': 'INFO',
#         #     'class': 'logging.FileHandler',
#         #     'filename': BASE_DIR / 'logs/django.log',
#         #     'formatter': 'verbose',
#         # },
#     },
#     'root': { # Catch-all logger
#         'handlers': ['console'], # Add 'file' handler here for production
#         'level': 'INFO', # Set to 'DEBUG' for development verbosity
#     },
#     'loggers': {
#         'django': { # Configure Django's internal loggers
#             'handlers': ['console'],
#             'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
#             'propagate': False, # Don't send django logs to the root logger as well
#         },
#         'courses': { # Example: Configure logging for your specific app
#             'handlers': ['console'],
#             'level': 'DEBUG', # Log DEBUG level messages from the courses app
#             'propagate': False,
#         },
#     },
# }
