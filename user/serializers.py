from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'first_name', 'last_name', 'phone', 'created_at')
        read_only_fields = ['created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        req = self.context.get('request')

        # Залишаємо роль USER, якщо неSTAFF
        if not req or not getattr(req.user, 'is_staff', False):
            validated_data['role'] = User.Role.USER

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        req = self.context.get('request')

        # Заборона зміни ролі для неSTAFF користувачів
        if 'role' in validated_data and (not req or not getattr(req.user, 'is_staff', False)):
            validated_data.pop('role')

        # Оновлюємо інші поля
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
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user
