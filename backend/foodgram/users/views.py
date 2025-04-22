from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from api.pagination import StandardResultsPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import AvatarSerializer

class UserViewSet(DjoserUserViewSet):
    """Представление для пользователей с дополнительной информацией о подписке и аватаре."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsPagination

    def get_permissions(self):
        """Настройка прав доступа в зависимости от выполняемого действия."""
        custom_actions = {"me", "avatar"}
        permission_classes = [IsAuthenticated] if self.action in custom_actions else self.permission_classes
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        user = request.user

        # Обработка DELETE запроса
        if request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response({"detail": "Аватар успешно удалён."}, status=status.HTTP_204_NO_CONTENT)

        # Обработка PUT запроса
        avatar_serializer = AvatarSerializer(data=request.data)
        if avatar_serializer.is_valid():
            avatar = avatar_serializer.validated_data['avatar']
            user.avatar = avatar  # Сохраняем изображение в поле avatar
            user.save()  # Сохраняем пользователя с новым аватаром
            return Response({"avatar": user.avatar.url}, status=status.HTTP_200_OK)

        return Response(avatar_serializer.errors, status=status.HTTP_400_BAD_REQUEST)