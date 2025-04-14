# src/apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegisterView, AdminUserViewSet, CurrentUserView

router = DefaultRouter()
# Register Admin User Management ViewSet
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'), # Keep if used
    # Include router URLs for admin user management
    path('', include(router.urls)),
]
