from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Ingredient(models.Model):
    """ Модель ингредиента """

    name = models.CharField(
        name='Название',
        max_length=100,
        blank=False,
        unique=True,

    )

    measurement_unit = models.CharField(
        name='Единица измерения',
        max_length=25,
        blank=False,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель рецепта """

    name = models.CharField(
        name='Название рецепта',
        max_length=150,
        blank=False,
        null=False,
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        blank=False,
        null=False,
    )

    image = models.ImageField(
        name='Фото блюда',
        upload_to='media/recipes/images/',
        blank=False,
        null=False,
    )

    text = models.TextField(
        name='Текст рецепта',
        blank=False,
        null=False,
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientRecipe',
        blank=False,
    )

    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(1,
                              "Время приготовления должно быть больше 1 минуты"
                              ),
        ],
        verbose_name="Время приготовления, мин",
        blank=False,
        null=False,
    )

    pub_date = models.DateTimeField(
        name='Дата добавления',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ('-pub_date',),
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """ Ингредиенты в рецепте """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        validators=[
            MinValueValidator(1,
                              "Количество должно быть числом более 1"
                              )
        ]
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f"{self.ingredient} для {self.recipe}"
