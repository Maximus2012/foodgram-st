from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewSet

# Создаём экземпляр DefaultRouter
router = DefaultRouter()

# Регистрируем viewset'ы
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    # Включаем маршруты для IngredientViewSet и RecipeViewSet
    path('', include(router.urls)),
]