from django_filters import rest_framework as filters
from .models import Ingredient, Recipe

class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по названию."""

    name = filters.CharFilter(field_name='name', lookup_expr='icontains', label='Название')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов по автору."""

    author = filters.NumberFilter(field_name="author_id")
    is_in_shopping_cart = filters.NumberFilter(method="filter_in_shopping_cart")
    is_favorited = filters.NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ['author']