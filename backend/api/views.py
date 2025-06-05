from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django_filters import rest_framework as filters
from django.db.models import Sum
from django.urls import reverse
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

from .filters import IngredientFilter, RecipeFilter
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

    def _handle_add_remove(self, model, request, pk, serializer_class=None):
        try:
            recipe_instance = self.get_object()
        except Recipe.DoesNotExist:
            raise NotFound("Рецепт не найден.")

        if request.method == "POST":
            already_added = model.objects.filter(user=request.user, recipe=recipe_instance).exists()
            if already_added:
                return Response(
                    {"errors": "Рецепт уже добавлен."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            model.objects.create(user=request.user, recipe=recipe_instance)
            serializer = (
                serializer_class(recipe_instance, context={"request": request})
                if serializer_class
                else RecipeReadSerializer(recipe_instance, context={"request": request})
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            user_recipe_relation = model.objects.filter(user=request.user, recipe=recipe_instance).first()
            if not user_recipe_relation:
                return Response(
                    {"errors": "Рецепт не найден в списке."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_recipe_relation.delete()
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
            Ingredient.objects.filter(ingredient_in_recipes__recipe__in=recipes)
            .values("name", "measurement_unit")
            .annotate(total_amount=Sum("ingredient_in_recipes__amount"))
            .order_by("name")
        )
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_type = request.query_params.get("file_type", "txt").lower()
        if file_type == "pdf":
            return self._create_pdf_response(recipes, ingredients, current_date)
        return self._create_txt_response(recipes, ingredients, current_date)

    def _create_pdf_response(self, recipes, ingredients, current_date):
        # Генерация PDF api/recipes/download_shopping_cart/?file_type=pdf
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.pdf"'
        pdf = canvas.Canvas(response, pagesize=letter)
        y = 750
        pdf.setFont("NTSomic-Bold", 15)
        y = self._draw_text(pdf, f"Корзина покупок (создана: {current_date}):", y)

        for recipe in recipes:
            y = self._draw_text(pdf, f"Автор: {recipe.author.username}", y)
            y = self._draw_text(pdf, f"Рецепт: {recipe.name}", y)
            y = self._draw_text(pdf, f"Текст: {recipe.text}", y)
            y = self._draw_text(
                pdf, f"Время приготовления: {recipe.cooking_time} мин.", y
            )
            y = self._draw_text(pdf, "Ингредиенты:", y)
            for ri in recipe.recipe_ingredients.all():
                line = f"- {ri.ingredient.name} - {ri.amount} {ri.ingredient.measurement_unit}"
                y = self._draw_text(pdf, line, y)
            y -= 10
            if y < 100:
                pdf.showPage()
                pdf.setFont("NTSomic-Bold", 15)
                y = 750
        y = self._draw_text(pdf, f"Всего рецептов в корзине: {recipes.count()}", y)
        y = self._draw_text(pdf, "Список ингредиентов для покупки:", y)
        for ing in ingredients:
            line = f"{ing['name']} - {ing['total_amount']} {ing['measurement_unit']}"
            y = self._draw_text(pdf, line, y)
            if y < 100:
                pdf.showPage()
                pdf.setFont("NTSomic-Bold", 15)
                y = 750
        pdf.save()
        return response

    def _draw_text(self, pdf_canvas, text_content, y_position, x_position=50, line_step=20):
        pdf_canvas.drawString(x_position, y_position, text_content)
        return y_position - line_step

    def _create_txt_response(self, recipes, ingredients, current_date):
        response = HttpResponse(content_type="text/plain", charset="utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        lines = [f"Корзина покупок (создана: {current_date}):\n"]
        for recipe in recipes:
            lines.append(f"Автор: {recipe.author.username}")
            lines.append(f"Рецепт: {recipe.name}")
            lines.append(f"Текст: {recipe.text}")
            lines.append(f"Время приготовления: {recipe.cooking_time} мин.")
            lines.append("Ингредиенты:")
            for ri in recipe.recipe_ingredients.all():
                lines.append(
                    f"- {ri.ingredient.name} - {ri.amount} {ri.ingredient.measurement_unit}"
                )
            lines.append("")
        lines.append(f"Всего рецептов в корзине: {recipes.count()}\n")
        lines.append("Список ингредиентов для покупки:")
        for ing in ingredients:
            lines.append(
                f"- {ing['name']} - {ing['total_amount']} {ing['measurement_unit']}"
            )
        response.write("\n".join(lines))
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

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[IsAuthenticated],
    )
    def get_link(self, request, pk):
        """
        Возвращает абсолютную короткую ссылку на рецепт по его идентификатору.
        """
        short_path = reverse("short-link", args=[pk])
        absolute_short_link = request.build_absolute_uri(short_path)
        return Response({"short-link": absolute_short_link})


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

        authors = User.objects.filter(subscribers__user=current_user)

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors, many=True, context={"request": request}
        )
        return Response(serializer.data)

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
