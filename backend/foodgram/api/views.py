from datetime import datetime

from django.db.models import Sum
from django.http import FileResponse
from django.urls import reverse
from django_filters import FilterSet, NumberFilter, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (
    Subscription, Recipe, Ingredient,
    ShoppingCart, Favorite, RecipeIngredient,
)
from users.models import User
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    UserProfileSerializer, AvatarSerializer,
    Pagination, UserSubscriptionSerializer,
    RecipeReadSerializer, RecipeWriteSerializer,
    RecipeShortSerializer, IngredientSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для пользователей. Наследуется от Djoser для добавления:
    - работы с аватаром;
    - подписок и отписок;
    - списка подписок.
    """
    pagination_class = Pagination
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        """
        Возвращает разрешения для действий.
        """
        if self.action in ["me", "avatar"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request, *args, **kwargs):
        """
        PUT — загрузка/обновление аватара.
        DELETE — удаление аватара.
        """
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": user.avatar.url}, status=200)

        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response({"detail": "Аватар успешно удалён."}, status=204)

        return Response({"detail": "Аватар отсутствует."}, status=400)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """
        Возвращает список подписок текущего пользователя с пагинацией.
        """
        user = request.user
        subscriptions = User.objects.filter(followers__user=user)

        paginator = self.paginator
        paginated = paginator.paginate_queryset(subscriptions, request)

        serializer = UserSubscriptionSerializer(
            paginated, many=True, context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """
        POST — подписаться на пользователя.
        DELETE — отписаться.
        """
        user = request.user
        author = self.get_object()

        if request.method == "POST":
            if user == author:
                return Response(
                    {"error": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {"error": f"Вы уже подписаны на пользователя {author.username}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserSubscriptionSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(user=user, author=author).first()
        if not subscription:
            return Response(
                {"error": "Вы не были подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipePagination(PageNumberPagination):
    """
    Пагинация рецептов с возможностью указания параметра ?limit.
    """
    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class RecipeFilter(FilterSet):
    """
    Фильтрация рецептов:
    - по автору;
    - по наличию в избранном;
    - по наличию в корзине.
    """
    author = NumberFilter(field_name="author_id")
    is_in_shopping_cart = NumberFilter(method="filter_in_shopping_cart")
    is_favorited = NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["author", "is_in_shopping_cart", "is_favorited"]

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset
        return queryset.filter(in_shopping_carts__user=user) if value == 1 else queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset
        return queryset.filter(in_favorites__user=user) if value == 1 else queryset


class RecipeViewSet(ModelViewSet):
    """
    CRUD-вьюсет для рецептов.
    Также реализованы действия:
    - добавление/удаление из избранного и корзины;
    - скачивание списка покупок;
    - получение короткой ссылки.
    """
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def toggle_relation(self, request, pk, model, error_message, success_message):
        """
        Общий метод для добавления/удаления рецепта в избранное или корзину.
        """
        user = request.user
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {"error": f"Рецепт с ID {pk} не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == "POST":
            obj, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {"error": error_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=user, recipe=recipe).first()
        if not obj:
            return Response(
                {"error": success_message.format(recipe.name)},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.toggle_relation(
            request, pk, ShoppingCart,
            error_message='Рецепт "{}" уже в корзине.',
            success_message='Рецепт "{}" отсутствует в корзине.'
        )

    @action(detail=True, methods=["post", "delete"], url_path="favorite", permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.toggle_relation(
            request, pk, Favorite,
            error_message='Рецепт "{}" уже в избранном.',
            success_message='Рецепт "{}" не найден в избранном.'
        )

    @action(detail=False, methods=["get"], url_path="download_shopping_cart", permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Возвращает файл .txt со списком покупок.
        """
        user = request.user
        cart_items = ShoppingCart.objects.filter(user=user).select_related("recipe")

        if not cart_items.exists():
            return Response({"error": "Ваша корзина пуста."}, status=400)

        recipe_ids = cart_items.values_list("recipe__id", flat=True)
        ingredients_qs = RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)

        ingredients_data = (
            ingredients_qs
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        recipes = Recipe.objects.filter(id__in=recipe_ids)
        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        header = f"Список покупок (составлен: {date_str})\n"
        product_header = "№ | Продукт | Кол-во | Ед. изм.\n"
        recipe_header = "\nИспользуется в рецептах:\n"

        products = [
            f"{i + 1} | {item['ingredient__name'].capitalize()} | {item['total_amount']} | {item['ingredient__measurement_unit']}"
            for i, item in enumerate(ingredients_data)
        ]

        recipe_list = [
            f"- {r.name} (Автор: {r.author.first_name} {r.author.last_name or r.author.username})"
            for r in recipes
        ]

        content = "\n".join([header, product_header, *products, recipe_header, *recipe_list])

        return FileResponse(
            content, as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain"
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """
        return Response(
            {
                "short-link": request.build_absolute_uri(
                    reverse("recipes:short_link", kwargs={"recipe_id": pk})
                )
            },
            status=status.HTTP_200_OK
        )


class IngredientFilter(FilterSet):
    """
    Фильтр для поиска ингредиентов по началу названия.
    """
    name = CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ["name"]


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет только для чтения ингредиентов.
    Позволяет искать по началу названия.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None