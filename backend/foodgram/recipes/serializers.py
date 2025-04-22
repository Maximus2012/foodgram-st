from rest_framework import serializers
from .models import Recipe, Ingredient, RecipeIngredient, User
from api.utils import Base64ImageField  # Убедитесь, что используете свой кастомный Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Количество ингредиента должно быть не меньше 1."
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']

class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()  # Поле для Base64 изображения
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Автоматически устанавливаем автором текущего пользователя
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'author', 'ingredients', 'image', 'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart']

    def create(self, validated_data):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            raise serializers.ValidationError({
                'author': 'Только авторизованные пользователи могут создавать рецепты.'
            })
        ingredients_data = self.initial_data.get('ingredients')
        validated_ingredients = RecipeCreateIngredientSerializer(data=ingredients_data, many=True)
        validated_ingredients.is_valid(raise_exception=True)
        validated_data.pop('recipe_ingredients', None)
        
        # Создаем рецепт, автор автоматически назначается через HiddenField
        recipe = Recipe.objects.create(**validated_data)

        # Присваиваем ингредиенты
        for ingredient in validated_ingredients.validated_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

        return recipe
    
    def update(self, instance, validated_data):
        ingredients_data = self.initial_data.get('ingredients')
        if ingredients_data is None:
            raise serializers.ValidationError(
                {"ingredients": "Поле ingredients обязательно при обновлении."}
            )

        validated_ingredients = RecipeCreateIngredientSerializer(data=ingredients_data, many=True)
        validated_ingredients.is_valid(raise_exception=True)

        # ❗ Удаляем поле recipe_ingredients, если оно случайно попало в validated_data
        validated_data.pop('recipe_ingredients', None)

        # Удаляем старые связи ингредиентов
        RecipeIngredient.objects.filter(recipe=instance).delete()

        # Обновляем остальные поля рецепта
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Добавляем новые ингредиенты
        for ingredient in validated_ingredients.validated_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

        return instance
    
    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно указать хотя бы один ингредиент.'
            })
        ingredient_ids = [int(item.get('id')) for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })
        return data

    def get_author(self, obj):
        """Получаем данные об авторе."""
        user = obj.author
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_subscribed': False,  # Можно добавить логику для проверки подписки
            'avatar': user.avatar.url if user.avatar else None
        }

    def get_is_favorited(self, obj):
        return False

    def get_is_in_shopping_cart(self, obj):
        return False

    def to_representation(self, instance):
        """Сериализация рецепта с включением всех полей."""
        representation = super().to_representation(instance)
        representation['author'] = self.get_author(instance)  # Добавляем авторов вручную в ответ
        return representation


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
