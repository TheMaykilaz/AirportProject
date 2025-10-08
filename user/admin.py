from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, EmailVerificationCode, LoginAttempt


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = [
        'passport_number', 'passport_expiry', 'passport_country',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
        'frequent_flyer_numbers', 'special_assistance',
        'email_notifications', 'sms_notifications', 'marketing_emails'
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_email_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'is_email_verified', 'is_phone_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Travel Preferences', {
            'fields': ('preferred_seat_class', 'dietary_restrictions'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Verification Status', {
            'fields': ('is_email_verified', 'is_phone_verified', 'google_id'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'passport_number', 'passport_expiry', 'emergency_contact_name')
    list_filter = ('passport_country', 'email_notifications', 'sms_notifications')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'passport_number')
    raw_id_fields = ('user',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code_type', 'code', 'is_used', 'expires_at', 'created_at')
    list_filter = ('code_type', 'is_used', 'created_at')
    search_fields = ('email', 'code')
    readonly_fields = ('code', 'created_at', 'expires_at')
    ordering = ('-created_at',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'attempt_type', 'status', 'ip_address', 'created_at')
    list_filter = ('attempt_type', 'status', 'created_at')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
