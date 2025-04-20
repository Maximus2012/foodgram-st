from django.shortcuts import redirect, get_object_or_404
from recipes.models import Recipe


def get_short_link(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на локальный URL рецепта.
    """

    # Получаем рецепт или возвращаем 404, если не найден
    get_object_or_404(Recipe, id=recipe_id)

    # Перенаправляем на локальный URL рецепта
    return redirect(f"/recipes/{recipe_id}/")
