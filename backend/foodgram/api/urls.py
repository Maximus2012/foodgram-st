from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    RecipeViewSet,
    IngredientViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]