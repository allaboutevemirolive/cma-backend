# backend/project/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# --- Swagger/OpenAPI Schema View ---
schema_view = get_schema_view(
   openapi.Info(
      title="Course Management API",
      default_version='v1',
      description="API for managing courses, including CRUD operations, filtering, and pagination.",
      terms_of_service="https://www.google.com/policies/terms/", # Replace with your terms
      contact=openapi.Contact(email="contact@courses.local"),    # Replace with your contact
      license=openapi.License(name="BSD License"),             # Replace with your license
   ),
   public=True,
   permission_classes=(permissions.AllowAny,), # Adjust permissions as needed
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('courses.urls')), # Include your app's API URLs under /api/

    # --- Swagger UI ---
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Optional: Add auth endpoints here for Bonus JWT
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
