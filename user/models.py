from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date
import secrets


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)

        if not extra_fields.get("username"):
            extra_fields["username"] = email.split("@")[0]

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'
        USER = 'user', 'User'
        PREMIUM = 'premium', 'Premium User'

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        PREFER_NOT_TO_SAY = 'N', 'Prefer not to say'

    # Core fields
    email = models.EmailField(unique=True, db_index=True)
    
    # Profile information
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')],
        help_text='Example: +1234567890 or +380501234567'
    )
    date_of_birth = models.DateField(null=True, blank=True, help_text="Required for flight bookings")
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    
    # Address information
    address_line1 = models.CharField(max_length=255, blank=True, help_text="Street address")
    address_line2 = models.CharField(max_length=255, blank=True, help_text="Apartment, suite, etc.")
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True, help_text="State or Province")
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Travel preferences
    preferred_seat_class = models.CharField(
        max_length=20,
        choices=[
            ('economy', 'Economy'),
            ('premium_economy', 'Premium Economy'),
            ('business', 'Business'),
            ('first', 'First Class'),
        ],
        default='economy',
        help_text="Default seat class preference"
    )
    dietary_restrictions = models.TextField(blank=True, help_text="Special dietary requirements")
    
    # OAuth and external integrations
    google_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    # User status and role
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        db_index=True
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def clean(self):
        super().clean()
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError("Date of birth cannot be in the future")
        
        # Validate age for flight bookings (minimum 13 years old)
        if self.date_of_birth:
            age = (date.today() - self.date_of_birth).days // 365
            if age < 13:
                raise ValidationError("Users must be at least 13 years old")

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_staff_member(self):
        return self.role in [self.Role.ADMIN, self.Role.STAFF]

    @property
    def is_premium_user(self):
        return self.role == self.Role.PREMIUM

    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def age(self):
        """Calculate user's age"""
        if not self.date_of_birth:
            return None
        return (date.today() - self.date_of_birth).days // 365

    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])

    def get_booking_count(self):
        """Get total number of bookings made by user"""
        return self.orders.count()

    def get_completed_flights(self):
        """Get number of completed flights"""
        return self.orders.filter(
            status='confirmed',
            tickets__status='completed'
        ).distinct().count()

    def can_book_flights(self):
        """Check if user can book flights (has required info)"""
        return bool(
            self.is_email_verified and
            self.first_name and
            self.last_name and
            self.date_of_birth
        )

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.get_role_display()}"


class EmailVerificationCode(models.Model):
    """
    Stores verification codes sent to users for passwordless email login.
    Codes expire after 10 minutes and can only be used once.
    """
    class CodeType(models.TextChoices):
        LOGIN = 'login', 'Login'
        EMAIL_VERIFICATION = 'email_verify', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6, db_index=True)
    code_type = models.CharField(max_length=15, choices=CodeType.choices, default=CodeType.LOGIN)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/device info")

    class Meta:
        db_table = 'email_verification_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'code_type', 'is_used']),
            models.Index(fields=['expires_at', 'is_used']),
        ]

    def __str__(self):
        return f"{self.email} - {self.get_code_type_display()} - {self.code} (used: {self.is_used})"

    @classmethod
    def generate_code(cls, email, code_type=CodeType.LOGIN, ip_address=None, user_agent="", expiry_minutes=10):
        """Generate a new 6-digit verification code for the given email."""
        # Invalidate previous unused codes of the same type
        cls.objects.filter(
            email=email,
            code_type=code_type,
            is_used=False
        ).update(is_used=True)
        
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        return cls.objects.create(
            email=email,
            code=code,
            code_type=code_type,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent[:500]  # Limit length
        )

    def is_valid(self):
        """Check if the code is still valid (not expired and not used)."""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_used(self):
        """Mark this code as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])

    @classmethod
    def cleanup_expired(cls):
        """Remove expired codes older than 24 hours"""
        cutoff = timezone.now() - timedelta(hours=24)
        cls.objects.filter(expires_at__lt=cutoff).delete()


class UserProfile(models.Model):
    """
    Extended user profile for additional travel-related information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Travel document information
    passport_number = models.CharField(max_length=20, blank=True, help_text="Passport number")
    passport_expiry = models.DateField(null=True, blank=True, help_text="Passport expiration date")
    passport_country = models.CharField(max_length=100, blank=True, help_text="Passport issuing country")
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Travel preferences
    frequent_flyer_numbers = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Frequent flyer numbers for different airlines"
    )
    special_assistance = models.TextField(blank=True, help_text="Special assistance requirements")
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile for {self.user.full_name}"

    @property
    def is_passport_valid(self):
        """Check if passport is valid (not expired)"""
        if not self.passport_expiry:
            return False
        return self.passport_expiry > date.today()

    def can_travel_internationally(self):
        """Check if user can travel internationally"""
        return bool(
            self.passport_number and 
            self.is_passport_valid and
            self.user.can_book_flights()
        )


class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring
    """
    class AttemptType(models.TextChoices):
        PASSWORD = 'password', 'Password Login'
        EMAIL_CODE = 'email_code', 'Email Code Login'
        GOOGLE_OAUTH = 'google_oauth', 'Google OAuth'

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        BLOCKED = 'blocked', 'Blocked'

    email = models.EmailField(db_index=True)
    attempt_type = models.CharField(max_length=15, choices=AttemptType.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.get_status_display()} ({self.created_at})"

    @classmethod
    def log_attempt(cls, email, attempt_type, status, ip_address, user_agent="", failure_reason=""):
        """Log a login attempt"""
        return cls.objects.create(
            email=email,
            attempt_type=attempt_type,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent[:500],
            failure_reason=failure_reason[:100]
        )

    @classmethod
    def get_recent_failures(cls, email, hours=1):
        """Get recent failed login attempts for an email"""
        since = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(
            email=email,
            status=cls.Status.FAILED,
            created_at__gte=since
        ).count()

    @classmethod
    def cleanup_old_attempts(cls, days=30):
        """Remove login attempts older than specified days"""
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(created_at__lt=cutoff).delete()



