from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from datetime import timedelta
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
        USER = 'user', 'User'

    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,

    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Write phone number')],
        help_text = 'Example +380501234567'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} -  ({self.role})"


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class EmailVerificationCode(models.Model):
    """
    Stores verification codes sent to users for passwordless email login.
    Codes expire after 10 minutes and can only be used once.
    """
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'email_verification_codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.code} (used: {self.is_used})"

    @classmethod
    def generate_code(cls, email, ip_address=None, expiry_minutes=10):
        """Generate a new 6-digit verification code for the given email."""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        return cls.objects.create(
            email=email,
            code=code,
            expires_at=expires_at,
            ip_address=ip_address
        )

    def is_valid(self):
        """Check if the code is still valid (not expired and not used)."""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_used(self):
        """Mark this code as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])



