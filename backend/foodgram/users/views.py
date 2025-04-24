from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import IsAuthenticated
from .models import User, Subscription
from .serializers import UserSerializer
from api.pagination import StandardResultsPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import AvatarSerializer, SubscriptionSerializer


class UserViewSet(DjoserUserViewSet):
    """Представление для пользователей с дополнительной информацией о подписке и аватаре."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsPagination

    def get_permissions(self):
        """Настройка прав доступа в зависимости от выполняемого действия."""
        custom_actions = {"me", "avatar"}
        permission_classes = (
            [IsAuthenticated]
            if self.action in custom_actions
            else self.permission_classes
        )
        return [permission() for permission in permission_classes]

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """Подписка и отписка на пользователя."""
        current_user = request.user
        target_user = self.get_object()

        if request.method == "POST":
            if current_user == target_user:
                return Response(
                    {"error": "Невозможно подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription_instance, is_new_subscription = (
                Subscription.objects.get_or_create(
                    user=current_user, author=target_user
                )
            )

            if not is_new_subscription:
                return Response(
                    {
                        "error": f"Вы уже подписаны на пользователя {target_user.username} (ID: {target_user.id})."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription_serializer = SubscriptionSerializer(
                target_user, context={"request": request}
            )
            return Response(
                subscription_serializer.data, status=status.HTTP_201_CREATED
            )

        subscription_instance = Subscription.objects.filter(
            user=current_user, author=target_user
        ).first()
        if not subscription_instance:
            return Response(
                {"error": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def subscriptions(self, request):
        current_user = request.user

        followed = Subscription.objects.filter(user=current_user).values_list(
            "author", flat=True
        )
        authors = User.objects.filter(id__in=followed)

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors, many=True, context={"request": request}
        )

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
            return Response(
                {"detail": "Аватар успешно удалён."}, status=status.HTTP_204_NO_CONTENT
            )

        # Обработка PUT запроса
        avatar_serializer = AvatarSerializer(data=request.data)
        if avatar_serializer.is_valid():
            avatar = avatar_serializer.validated_data["avatar"]
            user.avatar = avatar
            user.save()
            return Response({"avatar": user.avatar.url}, status=status.HTTP_200_OK)

        return Response(avatar_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
