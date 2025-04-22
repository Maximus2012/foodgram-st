from rest_framework import viewsets
from .models import Ingredient, Recipe
from .serializers import IngredientSerializer, RecipeSerializer
from .filters import IngredientFilter, RecipeFilter
from django_filters import rest_framework as filters
from api.pagination import StandardResultsPagination
from rest_framework.exceptions import NotFound, AuthenticationFailed
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import IsOwnerOrReadOnly

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией по имени."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = StandardResultsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            short_link = f"/recipes/{recipe.id}/"
            return Response({"short-link": short_link})
        except Recipe.DoesNotExist:
            raise NotFound(detail="Рецепт не найден")

    def create(self, request, *args, **kwargs):
        if request is None or request.user.is_anonymous:
            raise AuthenticationFailed('Только авторизованные пользователи могут создавать рецепты.')
        return super().create(request, *args, **kwargs)