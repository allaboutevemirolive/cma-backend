# src/config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta

# --- Base Directories ---
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# --- Environment Variables ---
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# --- Security Settings ---
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-fallback-change-me!")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
ALLOWED_HOSTS_STRING = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(",") if ALLOWED_HOSTS_STRING else []


# --- Application Definition ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-Party Apps
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_yasg",
    "corsheaders",
    "django_extensions",  # <-- ADD THIS LINE

    # Your Project's Apps
    "apps.courses.apps.CoursesConfig",
    "apps.profiles.apps.ProfilesConfig",
    "apps.enrollments.apps.EnrollmentsConfig",
    "apps.quizzes.apps.QuizzesConfig",
    # "apps.users", # Add this if your users app has models/admin/commands
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- Root URLConf ---
ROOT_URLCONF = "config.urls"

# --- Templates ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- WSGI & ASGI ---
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=os.getenv("DB_SSL_REQUIRE", "False").lower() == "true",
        )
    }
else:
    print(
        "WARNING: DATABASE_URL environment variable not found. Falling back to SQLite database at project root."
    )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": PROJECT_ROOT / "db.sqlite3",
        }
    }

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = "/static/"
STATIC_ROOT = PROJECT_ROOT / "staticfiles"

# --- Media Files ---
MEDIA_URL = "/media/"
MEDIA_ROOT = PROJECT_ROOT / "media"

# --- Default Primary Key Field Type ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework Settings ---
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# --- Simple JWT Settings ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
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
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'JWT Token (Prefix with "Bearer "). Example: "Bearer eyJ..."',
        }
    },
    "USE_SESSION_AUTH": False,
    "JSON_EDITOR": True,
    "SHOW_REQUEST_HEADERS": True,
    "SUPPORTED_SUBMIT_METHODS": ["get", "post", "put", "patch", "delete"],
}
LOGIN_URL = "/admin/login/"
LOGOUT_URL = "/admin/logout/"

# --- CORS Settings ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Allow your Vite frontend origin
    "http://127.0.0.1:5173",  # Also allow this, just in case
    "http://localhost:3000"
    # Add any other frontend origins if needed (e.g., production domain)
]

# Optional: Allow specific headers if needed (usually defaults are fine)
# CORS_ALLOW_HEADERS = [...]

# Optional: Allow specific methods (usually defaults are fine)
# CORS_ALLOW_METHODS = [...]

# Optional: Allow credentials (like cookies) if using session auth with CORS
# CORS_ALLOW_CREDENTIALS = True

# Alternative for quick development (LESS SECURE - allows ANY origin)
# WARNING: Do NOT use this in production!
# CORS_ALLOW_ALL_ORIGINS = True

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
