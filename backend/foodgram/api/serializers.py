import base64
import re

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import Recipe, Ingredient, RecipeIngredient
from users.models import User, Subscription
from .utils import Base64ImageField


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
        min_value=min_amount_of_ingredients,
        error_messages={
            f"min_value": f"Количество ингредиента должно быть не меньше {min_amount_of_ingredients}."
        },
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
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

    def validate(self, data):
        ingredients = self.initial_data.get("ingredients")
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

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()

            self._create_ingredients(instance, ingredients_data)

        return instance

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

    def get_is_subscribed(self, user_obj):
        current_user = self.context["request"].user
        if not current_user.is_authenticated:
            return False
        return Subscription.objects.filter(user=current_user, author=user_obj).exists()

    def get_avatar(self, user_obj):
        return user_obj.avatar.url if user_obj.avatar else ""


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

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return obj.marked_as_favorite.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return obj.added_to_carts.filter(user=user).exists()


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

    avatar = serializers.CharField(write_only=True, required=True)

    def validate_avatar(self, base64_string):
        """Декодируем base64 и создаём файл-объект."""
        if not base64_string:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")

        try:
            format, img_str = base64_string.split(";base64,")
            ext = format.split("/")[-1]
            decoded_img = base64.b64decode(img_str)
        except Exception:
            raise serializers.ValidationError("Некорректный формат изображения.")

        return ContentFile(decoded_img, name=f"user_avatar.{ext}")


class RecipeForSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в подписке."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "avatar",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        current_user = self.context["request"].user
        return Subscription.objects.filter(user=current_user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        queryset = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[: int(recipes_limit)]
        return RecipeForSubscriptionSerializer(
            queryset, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
