from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers as drf_serializers


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,  # password is optional (for Google OAuth2 users)
        min_length=8
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "role",
            "first_name",
            "last_name",
            "phone",
            "created_at",
        )
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        req = self.context.get("request")

        # Default new users to "user" role unless staff
        if not req or not getattr(req.user, "is_staff", False):
            validated_data["role"] = User.Role.USER

        user = User.objects.create_user(**validated_data)
        if password:  # Set password only if provided
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        req = self.context.get("request")

        # Prevent non-staff users from changing role
        if "role" in validated_data and (not req or not getattr(req.user, "is_staff", False)):
            validated_data.pop("role")

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "google_id",
            "phone",
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


class EmailLoginRequestSerializer(serializers.Serializer):
    """Serializer for requesting a verification code via email."""
    email = serializers.EmailField(required=True)


class EmailLoginVerifySerializer(serializers.Serializer):
    """Serializer for verifying the email code and logging in."""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
