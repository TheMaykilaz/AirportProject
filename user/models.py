from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'


    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,

    )
    phone = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Напишіть номер телефону')],
        help_text = 'Приклад +380501234567'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} -  ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN



