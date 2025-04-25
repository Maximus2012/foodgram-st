from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        "Название рецепта",
        max_length=80,
        blank=False,
        help_text="Введите название рецепта",
    )
    text = models.TextField(
        verbose_name="Описание приготовления",
        help_text="Опишите процесс приготовления",
    )
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Картинка")
    cooking_time = models.PositiveIntegerField(
        "Время приготовления (в минутах)",
        validators=[MinValueValidator(1)],
        help_text="Укажите время приготовления в минутах",
    )
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="used_in_recipes",
        verbose_name="Ингредиенты",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время публикации",
    )
    
    class Meta:
        ordering = ("-created_at", "name")
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        verbose_name="Название ингредиента",
        help_text="Введите название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=20,
        verbose_name="Единица измерения",
        help_text="Введите единицу измерения (например, граммы, мл, шт.)",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class RecipeIngredient(models.Model):
    """Связующая модель между рецептами и ингредиентами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_in_recipes",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1)],
        help_text="Укажите количество ингредиента",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient_pair",
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} — {self.amount} {self.ingredient.measurement_unit} в рецепте '{self.recipe.name}'"


class ShoppingCart(models.Model):
    """Хранилище рецептов, добавленных пользователем для покупки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Покупатель",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="added_to_carts",
        verbose_name="Выбранный рецепт",
    )

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_recipe_in_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} добавил в покупки: {self.recipe.name}"


class Favorite(models.Model):
    """Модель для хранения избранных рецептов пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="liked_recipes",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="marked_as_favorite",
        verbose_name="Избранный рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"
        ordering = ["user"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite_combination"
            )
        ]

    def __str__(self):
        return f"{self.user.username} в избранном: {self.recipe.name}"
