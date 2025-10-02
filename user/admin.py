from django.contrib import admin
from .models import User, EmailVerificationCode


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'created_at', 'expires_at', 'is_used', 'ip_address']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'code']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
