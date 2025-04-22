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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]
    
    class Meta:
        ordering = ["username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username

class Subscription(models.Model):
    """Модель, отражающая отношение подписки между пользователями."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь, который подписывается",
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь, на которого подписываются",
        related_name="subscribers",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription"
            ),
            models.UniqueConstraint(
                name="no_duplicate_subscriptions",
                condition=models.Q(),
                fields=["user", "author"],
            ),
        ]

    def __str__(self):
        return "{} → {}".format(self.user.get_username(), self.author.get_username())