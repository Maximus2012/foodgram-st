from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтрация для ингредиентов."""

    name = filters.CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов по автору, наличию в корзине и избранном."""

    is_in_shopping_cart = filters.NumberFilter(method="filter_in_shopping_cart")
    is_favorited = filters.NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["author"]

    def filter_in_shopping_cart(self, queryset, name, value):
        if (
            value
            and hasattr(self.request, "user")
            and self.request.user.is_authenticated
        ):
            return queryset.filter(added_to_carts__user=self.request.user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if (
            value
            and hasattr(self.request, "user")
            and self.request.user.is_authenticated
        ):
            return queryset.filter(marked_as_favorite__user=self.request.user)
        return queryset
