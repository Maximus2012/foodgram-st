from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet

router = DefaultRouter()

router.register(r"users", UserViewSet)


urlpatterns = [
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
