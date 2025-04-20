from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка для кастомного пользователя"""

    # Определяем поля для отображения в списке пользователей
    list_display = (
        "id",
        "username",
        "email",
        "get_full_name",
        "get_avatar",
        "get_recipe_count",
        "get_followers_count",
        "get_following_count",
    )

    # Поиск по полям
    search_fields = ("email", "username", "first_name", "last_name")

    # Порядок сортировки
    ordering = ("id",)

    # Фильтры для списка пользователей
    list_filter = ("is_staff", "is_superuser", "is_active")

    # Настройка полей на странице редактирования
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {"fields": ("username", "first_name", "last_name", "avatar")},
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    # Настройка полей для создания нового пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # Метод для отображения ФИО пользователя
    @admin.display(description="ФИО")
    def get_full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    # Метод для отображения аватара пользователя
    @admin.display(description="Аватар")
    @mark_safe
    def get_avatar(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50" style="border-radius: 50%;" />'
        return "Нет аватара"

    # Метод для отображения количества рецептов пользователя
    @admin.display(description="Рецептов")
    def get_recipe_count(self, user):
        return user.recipes.count()

    # Метод для отображения количества подписчиков пользователя
    @admin.display(description="Подписчиков")
    def get_followers_count(self, user):
        return user.followers.count()

    # Метод для отображения количества подписок пользователя
    @admin.display(description="Подписок")
    def get_following_count(self, user):
        return user.following.count()
