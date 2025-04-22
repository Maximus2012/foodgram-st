from rest_framework import viewsets
from .models import Ingredient, Recipe, ShoppingCart
from .serializers import IngredientSerializer, RecipeSerializer
from .filters import IngredientFilter, RecipeFilter
from django_filters import rest_framework as filters
from api.pagination import StandardResultsPagination
from rest_framework.exceptions import NotFound, AuthenticationFailed
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse, JsonResponse
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime

pdfmetrics.registerFont(TTFont('NTSomic-Bold', 'fonts/NTSomic-Regular.ttf'))


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией по имени."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = StandardResultsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            short_link = f"/recipes/{recipe.id}/"
            return Response({"short-link": short_link})
        except Recipe.DoesNotExist:
            raise NotFound(detail="Рецепт не найден")

    @action(detail=True, methods=['post'], url_path='shopping_cart', permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, pk=None):
        if request.user.is_anonymous:
            raise AuthenticationFailed("Необходимо войти в систему.")
        
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            raise NotFound("Рецепт не найден.")


        # Проверяем, не находится ли уже в корзине
        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": "Рецепт уже добавлен в корзину."}, status=400)

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        data = RecipeSerializer(recipe).data
        return Response(data, status=201)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart', permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart_items:
            return JsonResponse({"detail": "Корзина пуста."}, status=400)

        recipes = [item.recipe for item in shopping_cart_items]
        recipe_data = RecipeSerializer(recipes, many=True).data

        # Определяем тип файла (PDF или TXT)
        file_type = request.query_params.get('file_type', 'txt').lower()

        # Получаем текущую дату и время

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if file_type == 'pdf':
            # Генерация PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'

            pdf_canvas = canvas.Canvas(response, pagesize=letter)
            y_position = 750
            
            # Используем шрифт, который поддерживает кириллицу (например, Times-Roman)
            pdf_canvas.setFont("NTSomic-Bold", 15)
            
            pdf_canvas.drawString(50, y_position, f"Дата создания корзины: {current_date}")
            y_position -= 30
            pdf_canvas.drawString(50, y_position, f"Корзина рецептов")
            y_position -= 60
            for recipe in recipe_data:
                # Автор и дата создания корзины
                author = recipe.get('author', {})
                pdf_canvas.drawString(50, y_position, f"Автор: {author.get('username', '')}")
                y_position -= 20


                # Детали рецепта
                pdf_canvas.drawString(50, y_position, f"Рецепт: {recipe.get('name', '')}")
                y_position -= 20
                pdf_canvas.drawString(50, y_position, f"Время приготовления: {recipe.get('cooking_time', '')} минут")
                y_position -= 20

                # Ингредиенты
                pdf_canvas.drawString(50, y_position, "Ингредиенты:")
                y_position -= 20
                for ingredient in recipe.get('ingredients', []):
                    pdf_canvas.drawString(
                        50,
                        y_position,
                        f"{ingredient.get('name', '')} - {ingredient.get('amount', '')} {ingredient.get('measurement_unit', '')}"
                    )
                    y_position -= 20
                    if y_position < 50:  # Новый лист, если не хватает места
                        pdf_canvas.showPage()
                        y_position = 750  # Сбросить позицию на начало страницы
                y_position -= 20
            pdf_canvas.save()
            return response

        else:
            # Генерация TXT
            response = HttpResponse(content_type='text/plain', charset='utf-8')
            response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

            txt_data = f"Корзина покупок (создана: {current_date}):\n"
            for recipe in recipe_data:
                # Автор и дата создания корзины
                author = recipe.get('author', {})
                txt_data += f"Автор: {author.get('username', '')}\n"
                txt_data += f"Дата создания корзины: {current_date}\n"

                # Детали рецепта
                txt_data += f"Рецепт: {recipe.get('name', '')}\n"
                txt_data += f"Время приготовления: {recipe.get('cooking_time', '')} минут\n"

                # Ингредиенты
                txt_data += "Ингредиенты:\n"
                for ingredient in recipe.get('ingredients', []):
                    txt_data += f"{ingredient.get('name', '')} - {ingredient.get('amount', '')} {ingredient.get('measurement_unit', '')}\n"

                txt_data += "\n"  # Добавляем разделение между рецептами

            response.write(txt_data)
            return response

    def create(self, request, *args, **kwargs):
        if request is None or request.user.is_anonymous:
            raise AuthenticationFailed('Только авторизованные пользователи могут создавать рецепты.')
        return super().create(request, *args, **kwargs)