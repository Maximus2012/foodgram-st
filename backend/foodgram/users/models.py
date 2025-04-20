from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя, использующая стандартные таблицы Django"""

    email = models.EmailField("Email", unique=True, max_length=254)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    username = models.CharField(
        "Псевдоним",
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9@.+-_]+$",
                message="Имя пользователя может содержать только буквы, цифры и @/./+/-/_",
                code="invalid_username",
            )
        ],
    )
    avatar = models.ImageField(
        "Аватар", upload_to="users/avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["email"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
