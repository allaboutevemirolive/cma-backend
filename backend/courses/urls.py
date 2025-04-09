# backend/courses/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course') # basename is important if queryset changes

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
