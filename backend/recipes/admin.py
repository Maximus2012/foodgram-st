from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from .constants import DEFAULT_EMPTY_INGREDIENT_FORMS, MIN_INGREDIENT_COUNT


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = DEFAULT_EMPTY_INGREDIENT_FORMS
    autocomplete_fields = ["ingredient"]
    min_num = MIN_INGREDIENT_COUNT
    verbose_name = "Ингредиент"
    verbose_name_plural = "Ингредиенты"
    fields = ("ingredient", "amount")
    show_change_link = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name')
    ordering = ("name",)
    inlines = [RecipeIngredientInline]

    def favorites_count(self, recipe):
        return Favorite.objects.filter(recipe=recipe).count()
    favorites_count.short_description = "Добавлений в избранное"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")
    list_filter = ("ingredient",)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user",)
