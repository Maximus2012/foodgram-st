from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_link
from api.views import IngredientViewSet, RecipeViewSet
router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('recipes/<int:pk>/get-link/', get_link, name='recipe-get-link'),
]
