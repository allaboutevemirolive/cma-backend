# backend/project/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url # For parsing DATABASE_URL
from datetime import timedelta # For JWT token lifetime

# --- Base Directory ---
# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR points to the 'backend' directory where manage.py resides.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment Variables ---
# Load environment variables from .env file located in the BASE_DIR (backend directory)
# Example .env content:
# SECRET_KEY='your-very-secret-key-replace-me!'
# DEBUG=True
# ALLOWED_HOSTS=localhost,127.0.0.1
# DATABASE_URL=postgres://course_user:course_password@db:5432/course_db
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- Security Settings ---
# SECURITY WARNING: keep the secret key used in production secret!
# It's highly recommended to set this in your .env file and not hardcode it.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-for-dev-only-change-me!')

# SECURITY WARNING: don't run with debug turned on in production!
# Set DEBUG=False in your .env file for production environments.
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Define allowed hosts via .env, defaulting to localhost for development.
# For production, set this to your domain name(s) in .env
# Example .env: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS_STRING = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []
# If running behind a proxy, you might need to configure SECURE_PROXY_SSL_HEADER


# --- Application Definition ---
# List of Django apps and third-party apps used by the project.
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',          # The admin site
    'django.contrib.auth',           # Authentication framework
    'django.contrib.contenttypes',   # Content type framework
    'django.contrib.sessions',       # Session framework
    'django.contrib.messages',       # Messaging framework
    'django.contrib.staticfiles',    # Framework for managing static files (CSS, JS, images)

    # Third-Party Apps
    'rest_framework',                # Django REST Framework core
    'rest_framework_simplejwt',      # JWT token authentication
    # 'rest_framework_simplejwt.token_blacklist', # Optional: Uncomment if you need token blacklisting for logout
    'django_filters',                # Filtering capabilities for DRF views
    'drf_yasg',                      # OpenAPI/Swagger documentation generation

    # Your Project's Apps
    'courses.apps.CoursesConfig',    # Your courses application config
]

# --- Middleware ---
# Order matters here. Middleware processes requests/responses sequentially.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',          # Adds several security enhancements
    'django.contrib.sessions.middleware.SessionMiddleware',     # Enables session support
    'django.middleware.common.CommonMiddleware',              # Handles common tasks, like adding trailing slashes
    'django.middleware.csrf.CsrfViewMiddleware',              # Cross Site Request Forgery protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Associates users with requests
    'django.contrib.messages.middleware.MessageMiddleware',     # Enables the messages framework
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Protects against clickjacking attacks
]

# --- URL Configuration ---
# Points to the main urls.py file (project/urls.py) which defines the URL routes.
ROOT_URLCONF = 'project.urls'

# --- Templates ---
# Configuration for Django's template engine (mainly used for Admin site here).
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # No project-level template directories defined here
        'APP_DIRS': True, # Allows Django to look for templates inside installed apps' 'templates' directories
        'OPTIONS': {
            'context_processors': [ # Functions adding variables to template context
                'django.template.context_processors.debug',      # Adds DEBUG flag and sql_queries
                'django.template.context_processors.request',    # Adds the HttpRequest object
                'django.contrib.auth.context_processors.auth',     # Adds the user and perms objects
                'django.contrib.messages.context_processors.messages', # Adds messages from the messages framework
            ],
        },
    },
]

# --- WSGI ---
# Entry point for WSGI-compatible web servers to serve the application.
WSGI_APPLICATION = 'project.wsgi.application'


# --- Database ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# Configuration is read from the DATABASE_URL environment variable using dj-database-url.
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        # The 'default' database connection.
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600, # Optional: Keep connections open for 10 minutes
            # Set ssl_require=True in .env if connecting to a DB requiring SSL
            ssl_require=os.getenv('DB_SSL_REQUIRE', 'False').lower() == 'true'
        )
    }
else:
    # Fallback for environments where DATABASE_URL is not set (e.g., initial setup without .env).
    # Avoid using SQLite in production with Docker/PostgreSQL setup.
    print("WARNING: DATABASE_URL environment variable not found. Falling back to SQLite. "
          "Ensure DATABASE_URL is set in your .env file for Docker deployment.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# --- Password Validation ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
# Defines validators used to check user password strength.
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# --- Internationalization & Localization ---
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us' # Default language
TIME_ZONE = 'UTC'       # Use UTC internally for consistency
USE_I18N = True         # Enable Django's translation system
USE_TZ = True           # Make datetimes timezone-aware


# --- Static Files ---
# https://docs.djangoproject.com/en/4.2/howto/static-files/
# Files like CSS, JavaScript, site images (part of the application code).
STATIC_URL = '/static/' # URL prefix for static files served by the web server
# STATIC_ROOT = BASE_DIR / 'staticfiles' # Used by 'collectstatic' in production deployments


# --- Media Files ---
# https://docs.djangoproject.com/en/4.2/topics/files/
# User-uploaded files (like course images).
MEDIA_URL = '/media/' # URL prefix for media files
# Absolute filesystem path where media files will be stored (inside the container).
MEDIA_ROOT = BASE_DIR / 'media'


# --- Default Primary Key Field Type ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
# Specifies the type of auto-created primary key fields.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' # Recommended default (64-bit integer)


# --- Django REST Framework Settings ---
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    # Default Pagination Style
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10, # Number of items to return per paginated page

    # Default Filtering Backend(s)
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend', # Enables filterset_fields
        'rest_framework.filters.SearchFilter',           # Enables search_fields (?search=...)
        'rest_framework.filters.OrderingFilter',         # Enables ordering_fields (?ordering=...)
    ),

    # Default Authentication Scheme(s)
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication', # Use JWT Bearer tokens for API auth
        # Add SessionAuthentication if you also need login via browsable API/admin alongside JWT
        # 'rest_framework.authentication.SessionAuthentication',
    ),

    # Default Permission Policy
    'DEFAULT_PERMISSION_CLASSES': [
        # Restrict API access to authenticated users by default.
        # Views can override this (e.g., AllowAny for public endpoints).
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Internal Schema Generation (usually not needed when using drf-yasg)
    # 'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',
}


# --- Simple JWT Settings (djangorestframework-simplejwt) ---
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
SIMPLE_JWT = {
    # Token Lifetimes
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Adjust as needed (e.g., 15-60 minutes)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),    # Adjust as needed (e.g., 1-30 days)

    # Token Rotation and Blacklisting (Enhanced Security)
    "ROTATE_REFRESH_TOKENS": False, # If True, refreshing issues a new refresh token
    "BLACKLIST_AFTER_ROTATION": False, # Requires 'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS

    "UPDATE_LAST_LOGIN": True, # Update user's last_login on token activity

    # Cryptography
    "ALGORITHM": "HS256",      # Algorithm used for signing tokens
    "SIGNING_KEY": SECRET_KEY, # Use the Django SECRET_KEY for HS256
    "VERIFYING_KEY": None,     # Not used for symmetric algorithms like HS256
    "AUDIENCE": None,          # Optional 'aud' claim
    "ISSUER": None,            # Optional 'iss' claim

    # Header and Payload Configuration
    "AUTH_HEADER_TYPES": ("Bearer",), # Expected prefix in the Authorization header
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION", # Header Django converts 'Authorization' to
    "USER_ID_FIELD": "id",            # User model field to use in payload
    "USER_ID_CLAIM": "user_id",       # JWT claim name for the user ID
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule", # Function to retrieve user

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",), # Token class for access tokens
    "TOKEN_TYPE_CLAIM": "token_type",   # Claim indicating 'access' or 'refresh'
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser", # Lightweight user representation from token

    "JTI_CLAIM": "jti", # JWT ID claim, unique for each token

    # Sliding Tokens (Alternative token refresh mechanism)
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5), # Initial lifetime
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1), # How long it remains refreshable
}


# --- drf-yasg (Swagger/OpenAPI) Settings ---
# https://drf-yasg.readthedocs.io/en/stable/settings.html
SWAGGER_SETTINGS = {
    # Authentication Setup for the Swagger UI itself
    'SECURITY_DEFINITIONS': {
        'Bearer': { # Arbitrary name for the security scheme
            'type': 'apiKey',           # Indicates a token sent in a header or query param
            'name': 'Authorization',    # The name of the HTTP header
            'in': 'header',             # Where the key is sent (header, query)
            'description': 'JWT Token (Prefix with "Bearer "). Example: "Bearer eyJ..."'
        }
        # Add other schemes (e.g., 'BasicAuth': {'type': 'basic'}) if needed
    },
    # Optional: Automatically apply a security scheme to locked endpoints in the UI
    # 'SECURITY_REQUIREMENTS': [{'Bearer': []}],

    # UI/Behavior Configuration
    'USE_SESSION_AUTH': False, # Do not use Django's session authentication for Swagger UI interactions
    'JSON_EDITOR': True,       # Use a rich JSON editor for request bodies
    'SHOW_REQUEST_HEADERS': True, # Display request headers (useful for auth debugging)
    'SUPPORTED_SUBMIT_METHODS': [ # HTTP methods that get the "Try it out" button
        'get', 'post', 'put', 'patch', 'delete'
    ],
    # 'DEFAULT_MODEL_RENDERING': 'example', # How models are shown ('model' or 'example')
    # 'VALIDATOR_URL': None, # Set to None to disable schema validation badge
}

# URLs needed by drf-yasg if using the login/logout buttons in the UI
LOGIN_URL = '/admin/login/'  # Redirect URL for Swagger login button
LOGOUT_URL = '/admin/logout/' # Redirect URL for Swagger logout button

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
