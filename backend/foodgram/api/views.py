from datetime import datetime

from django.http import HttpResponse, JsonResponse

from django_filters import rest_framework as filters

from django.db.models import Sum

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.response import Response

from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart

from api.serializers import AvatarSerializer, SubscriptionSerializer, UserSerializer

from .pagination import StandardResultsPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
)

from users.models import Subscription, User

pdfmetrics.registerFont(TTFont("NTSomic-Bold", "fonts/NTSomic-Regular.ttf"))


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией по имени."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = StandardResultsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        if self.action in [
            "add_to_favorite",
            "add_to_shopping_cart",
            "download_shopping_cart",
        ]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):

        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        self.perform_create(write_serializer)

        read_serializer = RecipeReadSerializer(
            write_serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)

        read_serializer = RecipeReadSerializer(
            write_serializer.instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def _handle_add_remove(self, model, request, pk, serializer_class=None):
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            raise NotFound("Рецепт не найден.")

        if request.method == "POST":
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=request.user, recipe=recipe)
            if serializer_class:
                serializer = serializer_class(recipe, context={"request": request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                serializer = RecipeReadSerializer(recipe, context={"request": request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            obj = model.objects.filter(user=request.user, recipe=recipe).first()
            if not obj:
                return Response(
                    {"errors": "Рецепт не найден в списке."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def add_to_shopping_cart(self, request, pk=None):
        return self._handle_add_remove(
            ShoppingCart, request, pk, serializer_class=ShortRecipeSerializer
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(user=user)

        if not shopping_cart_items.exists():
            return JsonResponse({"detail": "Корзина пуста."}, status=400)

        recipes = Recipe.objects.filter(
            id__in=shopping_cart_items.values_list("recipe_id", flat=True)
        ).prefetch_related("recipe_ingredients__ingredient", "author")

        ingredients = (
            recipes.values(
                "ingredients__name",
                "ingredients__measurement_unit",
            )
            .annotate(total_amount=Sum("recipe_ingredients__amount"))
            .order_by("ingredients__name")
        )

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_type = request.query_params.get("file_type", "txt").lower()

        if file_type == "pdf":
            # Генерация PDF api/recipes/download_shopping_cart/?file_type=pdf
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="shopping_cart.pdf"'

            pdf_canvas = canvas.Canvas(response, pagesize=letter)
            y_position = 750

            pdf_canvas.setFont("NTSomic-Bold", 15)
            pdf_canvas.drawString(
                50, y_position, f"Корзина покупок (создана: {current_date}):"
            )
            y_position -= 30
            for recipe in recipes:
                pdf_canvas.drawString(
                    50, y_position, f"Автор: {recipe.author.username}"
                )
                y_position -= 20
                pdf_canvas.drawString(50, y_position, f"Рецепт: {recipe.name}")
                y_position -= 20
                pdf_canvas.drawString(50, y_position, f"Текст: {recipe.text}")
                y_position -= 20
                pdf_canvas.drawString(
                    50, y_position, f"Время приготовления: {recipe.cooking_time} мин."
                )
                y_position -= 20
                pdf_canvas.drawString(50, y_position, f"Ингредиенты:")
                y_position -= 30

                for ri in recipe.recipe_ingredients.all():
                    pdf_canvas.drawString(
                        50,
                        y_position,
                        f"- {ri.ingredient.name} - {ri.amount} {ri.ingredient.measurement_unit}",
                    )
                    y_position -= 20
                y_position -= 30
                if y_position < 120:
                    pdf_canvas.showPage()
                    pdf_canvas.setFont("NTSomic-Bold", 15)
                    y_position = 750
            pdf_canvas.drawString(50, y_position, "Список ингредиентов для покупки")
            y_position -= 30

            for ingredient in ingredients:
                line = f"{ingredient['ingredients__name']} - {ingredient['total_amount']} {ingredient['ingredients__measurement_unit']}"
                pdf_canvas.drawString(50, y_position, line)
                y_position -= 30
                if y_position < 50:
                    pdf_canvas.showPage()
                    pdf_canvas.setFont("NTSomic-Bold", 15)
                    y_position = 750

            pdf_canvas.save()
            return response

        else:
            response = HttpResponse(content_type="text/plain", charset="utf-8")
            response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'

            txt_data = f"Корзина покупок (создана: {current_date}):\n\n"

            for recipe in recipes:
                txt_data += f"Автор: {recipe.author.username}\n"
                txt_data += f"Рецепт: {recipe.name}\n"
                txt_data += f"Текст: {recipe.text}\n"
                txt_data += f"Время приготовления: {recipe.cooking_time} мин.\n"
                txt_data += "Ингредиенты:\n"
                for ri in recipe.recipe_ingredients.all():
                    txt_data += f"- {ri.ingredient.name} - {ri.amount} {ri.ingredient.measurement_unit}\n"
                txt_data += "\n"

            txt_data += f"Всего рецептов в корзине: {recipes.count()}\n\n"

            ingredients = (
                Ingredient.objects.filter(ingredient_in_recipes__recipe__in=recipes)
                .values("name", "measurement_unit")
                .annotate(total_amount=Sum("ingredient_in_recipes__amount"))
                .order_by("name")
            )

            txt_data += "Итого ингредиентов:\n"
            for ingredient in ingredients:
                txt_data += f"- {ingredient['name']} - {ingredient['total_amount']} {ingredient['measurement_unit']}\n"

            response.write(txt_data)
            return response

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def add_to_favorite(self, request, pk=None):
        if request.method == "POST":
            try:
                recipe = self.get_object()
            except Recipe.DoesNotExist:
                raise NotFound("Рецепт не найден.")

            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в избранное."}, status=400
                )

            Favorite.objects.create(user=request.user, recipe=recipe)

            data = ShortRecipeSerializer(recipe).data
            return Response(data, status=201)

        elif request.method == "DELETE":
            try:
                recipe = self.get_object()
            except Recipe.DoesNotExist:
                raise NotFound("Рецепт не найден.")

            favorite_item = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).first()
            if not favorite_item:
                return Response({"detail": "Рецепт не найден в избранном."}, status=400)

            favorite_item.delete()
            return Response(status=204)


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

        if request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(
                {"detail": "Аватар успешно удалён."}, status=status.HTTP_204_NO_CONTENT
            )

        avatar_serializer = AvatarSerializer(data=request.data)
        if avatar_serializer.is_valid():
            avatar = avatar_serializer.validated_data["avatar"]
            user.avatar = avatar
            user.save()
            return Response({"avatar": user.avatar.url}, status=status.HTTP_200_OK)

        return Response(avatar_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
