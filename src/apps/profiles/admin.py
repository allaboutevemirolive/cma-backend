# src/apps/profiles/admin.py
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'status', 'updated_at')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'user__email')
