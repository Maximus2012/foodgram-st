from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Recipe


@api_view(["GET"])
def get_link(request, pk=None):
    try:
        recipe = Recipe.objects.get(pk=pk)
        short_link = f"/recipes/{recipe.id}/"
        return Response({"short-link": short_link})
    except Recipe.DoesNotExist:
        raise NotFound(detail="Рецепт не найден")