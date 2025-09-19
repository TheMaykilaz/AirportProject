from urllib import request

from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'first_name', 'last_name', 'phone', 'created_at')

        read_only_fields = ['created_at', ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        request = self.context.get('request')

        if not request or not request.user.is_authenticated or not request.user.is_staff:
            validated_data['role'] = User.Role.USER

        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if 'role' in validated_data:
            if not request or not request.user.is_authenticated or not request.user.is_staff:
                validated_data.pop('role', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if password:
                instance.set_password(password)

            instance.save()
            return instance



class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone')

    def create(self, validated_data):
        # user registers as plain USER, cannot set role
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user