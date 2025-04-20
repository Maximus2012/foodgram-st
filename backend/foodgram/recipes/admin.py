from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.models import (
    Recipe,
    Ingredient,
    Subscription,
    ShoppingCart,
    Favorite,
)


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени приготовления рецепта."""

    title = "Время готовки"
    parameter_name = "cooking_time_category"

    def lookups(self, request, model_admin):
        return [
            ("fast", "Быстрое (≤10 мин)"),
            ("medium", "Среднее (11–30 мин)"),
            ("long", "Долгое (>30 мин)"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "fast":
            return queryset.filter(cooking_time__lte=10)
        if self.value() == "medium":
            return queryset.filter(cooking_time__gt=10, cooking_time__lte=30)
        if self.value() == "long":
            return queryset.filter(cooking_time__gt=30)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка отображения модели Recipe в админке."""

    list_display = (
        "id",
        "name",
        "cooking_time",
        "get_author_name",
        "get_favorites_count",
        "get_ingredients",
        "get_image",
    )
    search_fields = (
        "name",
        "author__username",
        "author__first_name",
        "author__last_name",
    )
    list_filter = ("author", "name", CookingTimeFilter)

    @admin.display(description="Автор")
    def get_author_name(self, recipe):
        """Получение ФИО автора или его username."""
        return recipe.author.get_full_name() or recipe.author.username

    @admin.display(description="В избранном")
    def get_favorites_count(self, recipe):
        """Количество добавлений рецепта в избранное."""
        return recipe.favorites.count()

    @admin.display(description="Ингредиенты")
    def get_ingredients(self, recipe):
        """
        Отображение ингредиентов рецепта с количеством и единицей измерения.
        Используется HTML-разметка для переноса строк.
        """
        return mark_safe(
            "<br>".join(
                f"{item.ingredient.name} — {item.amount} {item.ingredient.measurement_unit}"
                for item in recipe.recipe_ingredients.all()
            )
        )

    @admin.display(description="Изображение")
    def get_image(self, recipe):
        """Отображение изображения рецепта в админке."""
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="75" height="75" />')
        return "Нет изображения"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка отображения модели Ingredient в админке."""

    list_display = ("id", "name", "measurement_unit", "get_recipe_count")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit",)
    ordering = ("name",)

    @admin.display(description="Используется в рецептах")
    def get_recipe_count(self, ingredient):
        """Количество рецептов, в которых используется ингредиент."""
        return ingredient.recipeingredient_set.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка отображения модели подписок в админке."""

    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user", "author")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка отображения модели корзины покупок в админке."""

    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка отображения модели избранного в админке."""

    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")
