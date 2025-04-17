from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        name='Email',
        verbose_name='Адрес электронной почты',
        max_length=100,
        unique=True,
    )
    first_name = models.CharField(
        name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        name='Фамилия',
        max_length=150
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email
