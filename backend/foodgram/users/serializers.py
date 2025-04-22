from rest_framework import serializers
from .models import User, Subscription
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.core.exceptions import ValidationError
import re
from django.core.files.base import ContentFile
import base64
from recipes.serializers import RecipeSerializer
from recipes.models import Recipe

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
            raise ValidationError("Поле `username` не соответствует требуемому формату.")
        return value
    

class AvatarSerializer(serializers.Serializer):
    """Сериализатор для обработки изображения в формате Base64."""
    
    avatar = serializers.CharField(write_only=True, required=True)

    def validate_avatar(self, base64_string):
        """Декодируем base64 и создаём файл-объект."""
        if not base64_string:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")
        
        try:
            format, img_str = base64_string.split(";base64,")  # Разделяем на формат и строку base64
            ext = format.split("/")[-1]  # Получаем расширение файла
            decoded_img = base64.b64decode(img_str)  # Декодируем строку в изображение
        except Exception:
            raise serializers.ValidationError("Некорректный формат изображения.")

        return ContentFile(decoded_img, name=f"user_avatar.{ext}")


# Новый сериализатор для рецептов в подписке (только нужные поля)
class RecipeForSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "first_name", "last_name",
            "email", "is_subscribed", "avatar",
            "recipes", "recipes_count"
        )

    def get_is_subscribed(self, obj):
        current_user = self.context["request"].user
        return Subscription.objects.filter(user=current_user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        queryset = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        return RecipeForSubscriptionSerializer(queryset, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()