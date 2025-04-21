from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Класс для описания модели User."""

    username = models.CharField(
        "Логин",
        unique=True,
        blank=False,
        max_length=100)
    first_name = models.CharField(
        "Имя",
        blank=False,
        max_length=30,
    )
    last_name = models.CharField(
        "Фамилия",
        blank=False,
        max_length=30)
    email = models.EmailField(
        "Адрес почты",
        unique=True,
        blank=False,
        max_length=60
    )
    avatar = models.ImageField(
        "Иконка",
        blank=True,
        null=True,
        upload_to="avatars/users/"
    )

    class Meta:
        ordering = ["username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username
