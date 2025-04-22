from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Создаём экземпляр DefaultRouter
router = DefaultRouter()

# Регистрируем UserViewSet без basename, если оно не требуется
router.register(r'users', UserViewSet)  # basename можно опустить, если он не нужен

urlpatterns = [
    # Включаем маршруты для аутентификации от Djoser
    path("auth/", include("djoser.urls")),  # Включаем стандартные маршруты Djoser
    path("auth/", include("djoser.urls.authtoken")),  # Включаем маршрут для токенов
    
    # Включаем маршруты для UserViewSet
    path('', include(router.urls)),
]