import re

from django.core.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe, Ingredient, RecipeIngredient
from users.models import User
from .constants import MIN_AMOUNT_OF_INGREDIENTS


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_OF_INGREDIENTS,
        error_messages={
            "min_value": f"Количество ингредиента должно быть не меньше {MIN_AMOUNT_OF_INGREDIENTS}."
        },
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = RecipeCreateIngredientSerializer(many=True, write_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "author",
            "ingredients",
            "image",
            "text",
            "cooking_time",
        ]

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Поле 'image' не может быть пустым.")
        return value

    def validate(self, data):
        ingredients = self.initial_data.get("ingredients")

        if ingredients is None:
            raise serializers.ValidationError(
                {"ingredients": "Поле 'ingredients' обязательно."}
            )

        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Нужно указать хотя бы один ингредиент."}
            )

        ingredient_ids = [int(item.get("id")) for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self._create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class UserSerializer(DjoserUserSerializer):
    """Расширенный сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, author):
        current_user = self.context["request"].user
        if not current_user.is_authenticated:
            return False
        return author.subscribers.filter(user=current_user).exists()

    def get_avatar(self, author):
        return author.avatar.url if author.avatar else ""


class RecipeReadSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, source="recipe_ingredients")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "author",
            "ingredients",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def get_is_favorited(self, recipe):
        current_user = self.context.get("request").user
        if current_user.is_anonymous:
            return False
        return recipe.marked_as_favorite.filter(user=current_user).exists()

    def get_is_in_shopping_cart(self, recipe):
        current_user = self.context.get("request").user
        if current_user.is_anonymous:
            return False
        return recipe.added_to_carts.filter(user=current_user).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор регистрации пользователя с валидацией username."""

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        )

    def validate_username(self, value):
        """Проверка, что значение username соответствует регулярному выражению."""
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise ValidationError(
                "Поле `username` не соответствует требуемому формату."
            )
        return value


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для обработки изображения в формате Base64."""

    avatar = Base64ImageField(required=True)

    def validate_avatar(self, value):
        """Декодируем base64 и создаём файл-объект."""
        if not value:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")
        return value


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, author):
        current_user = self.context["request"].user
        if current_user.is_anonymous:
            return False
        return author.subscribers.filter(user=current_user).exists()

    def get_recipes(self, author):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        author_recipes = author.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            author_recipes = author_recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(
            author_recipes, many=True, context=self.context
        ).data
