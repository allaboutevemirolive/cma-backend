# backend/project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings            # To access settings variables
from django.conf.urls.static import static  # To serve media files in development

# --- drf-yasg (Swagger/OpenAPI) ---
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# --- Simple JWT (Token Authentication) ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --- Schema View Configuration (for drf-yasg) ---
schema_view = get_schema_view(
   openapi.Info(
      title="Course Management API",
      default_version='v1',
      description="API for managing courses, including CRUD operations, filtering, pagination, JWT authentication, and image uploads.",
      terms_of_service="https://www.example.com/policies/terms/", # Replace with your actual terms URL
      contact=openapi.Contact(email="contact@example.com"),    # Replace with your contact email
      license=openapi.License(name="BSD License"),             # Replace with your chosen license
   ),
   public=True, # Set to False if you want schema only accessible to logged-in users (e.g., in production)
   permission_classes=(permissions.AllowAny,), # Adjust permissions for schema access if needed
)

# --- URL Patterns ---
urlpatterns = [
    # 1. Django Admin Site
    path('admin/', admin.site.urls),

    # 2. API Endpoints
    # Include URLs from the 'courses' app, prefixed with 'api/'
    path('api/', include('courses.urls')),

    # 3. JWT Authentication Endpoints
    # POST to /api/token/ with username/password to get access/refresh tokens
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # POST to /api/token/refresh/ with refresh token to get a new access token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 4. API Documentation Endpoints (drf-yasg)
    # JSON and YAML schema views (useful for code generation tools)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'), # format can be .json or .yaml
    # Swagger UI browser interface
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # ReDoc UI browser interface (alternative documentation style)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]

# --- Media File Serving (Development Only) ---
# This is crucial for serving files uploaded via ImageField/FileField during development.
# In production, your web server (like Nginx) should be configured to serve these files directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- Static File Serving (Development Only) ---
# Django's runserver automatically serves static files when DEBUG=True if django.contrib.staticfiles is in INSTALLED_APPS.
# However, explicitly adding it can sometimes be helpful or required depending on setup.
# if settings.DEBUG:
#    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Only needed if STATIC_ROOT is defined and collectstatic has been run
