from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet,
                    RecipeViewSet,
                    UserViewSet)

router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet, basename='recipe')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r"users", UserViewSet, basename='user')

urlpatterns = [
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path('', include(router.urls)),
]
