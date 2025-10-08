from rest_framework import serializers
from .models import User, UserProfile, EmailVerificationCode, LoginAttempt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers as drf_serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    
    class Meta:
        model = UserProfile
        fields = [
            'passport_number', 'passport_expiry', 'passport_country',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'frequent_flyer_numbers', 'special_assistance',
            'email_notifications', 'sms_notifications', 'marketing_emails'
        ]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,  # password is optional (for Google OAuth2 users)
        min_length=8
    )
    profile = UserProfileSerializer(required=False)
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    booking_count = serializers.SerializerMethodField()
    can_book_flights = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "role",
            "first_name", "last_name", "phone", "date_of_birth", "gender",
            "address_line1", "address_line2", "city", "state_province", 
            "postal_code", "country", "preferred_seat_class", "dietary_restrictions",
            "is_email_verified", "is_phone_verified", "google_id",
            "created_at", "updated_at", "full_name", "age", "booking_count",
            "can_book_flights", "profile"
        ]
        read_only_fields = ["created_at", "updated_at", "id"]
        extra_kwargs = {
            'password': {'write_only': True},
            'google_id': {'read_only': True},
        }

    def get_booking_count(self, obj):
        return obj.get_booking_count()

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password", None)
        req = self.context.get("request")

        # Default new users to "user" role unless staff
        if not req or not getattr(req.user, "is_staff", False):
            validated_data["role"] = User.Role.USER

        user = User.objects.create_user(**validated_data)
        if password:  # Set password only if provided
            user.set_password(password)
            user.save()
        
        # Create profile if data provided
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password", None)
        req = self.context.get("request")

        # Prevent non-staff users from changing role
        if "role" in validated_data and (not req or not getattr(req.user, "is_staff", False)):
            validated_data.pop("role")

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        
        # Update or create profile
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Registration Example',
            summary='User registration example',
            description='Example data for user registration',
            value={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User"
            },
            request_only=True,
        )
    ]
)
class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Valid email address"
    )
    username = serializers.CharField(
        required=True,
        help_text="Unique username"
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username", 
            "password",
            "first_name",
            "last_name",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        # Map email field to expected username key
        email = attrs.get('email') or attrs.get('username')
        if not email:
            raise drf_serializers.ValidationError({'email': ['This field is required.']})
        attrs['username'] = email
        return super().validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Email Request Example',
            summary='Request verification code',
            description='Request a verification code to be sent to email',
            value={
                "email": "test@example.com"
            },
            request_only=True,
        )
    ]
)
class EmailLoginRequestSerializer(serializers.Serializer):
    """Serializer for requesting a verification code via email."""
    email = serializers.EmailField(
        required=True,
        help_text="Email address to send verification code to"
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Email Verify Example',
            summary='Verify email code',
            description='Verify the email verification code',
            value={
                "email": "test@example.com",
                "code": "123456"
            },
            request_only=True,
        )
    ]
)
class EmailLoginVerifySerializer(serializers.Serializer):
    """Serializer for verifying the email code and logging in."""
    email = serializers.EmailField(
        required=True,
        help_text="Email address that received the code"
    )
    code = serializers.CharField(
        required=True, 
        min_length=6, 
        max_length=6,
        help_text="6-digit verification code from email"
    )


class UserPublicSerializer(serializers.ModelSerializer):
    """Public user serializer with limited fields for display"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'first_name', 'last_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserStatsSerializer(serializers.ModelSerializer):
    """User statistics serializer for admin/analytics"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    booking_count = serializers.SerializerMethodField()
    completed_flights = serializers.SerializerMethodField()
    can_book_flights = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'age', 'country',
            'preferred_seat_class', 'is_email_verified', 'is_phone_verified',
            'booking_count', 'completed_flights', 'can_book_flights',
            'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']
    
    def get_booking_count(self, obj):
        return obj.get_booking_count()
    
    def get_completed_flights(self, obj):
        return obj.get_completed_flights()


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for login attempts (admin use)"""
    
    class Meta:
        model = LoginAttempt
        fields = [
            'id', 'email', 'attempt_type', 'status', 'ip_address',
            'failure_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
