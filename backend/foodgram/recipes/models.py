from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q, F
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


class Follow(models.Model):
    """ Подписки на авторов рецептов """
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Подписан',
        related_name='followed',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Мои подписки'
        verbose_name_plural = 'Мои подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following'),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='no_self_following')]

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.author}'


class Favorite(models.Model):
    """ Список покупок пользователя """
    author = models.ForeignKey(
        User,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта')
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Рецепты')

    class Meta:
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [models.UniqueConstraint(
            fields=['author', 'recipe'],
            name='unique_favorite')]

    def __str__(self):
        return f'{self.recipe}'


class ShoppingCart(models.Model):
    """ Список покупок пользователя """
    author = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        verbose_name='Рецепт для приготовления',
        on_delete=models.CASCADE,
        help_text='Выберите рецепт для приготовления')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [models.UniqueConstraint(
            fields=['author', 'recipe'],
            name='unique_cart')]

    def __str__(self):
        return f'{self.recipe}'
