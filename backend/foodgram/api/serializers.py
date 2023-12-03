import base64

import djoser.serializers
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from recipes.models import (MIN_AMOUNT, MIN_COOKING_TIME, Favorite, Ingredient,
                            Purchase, Recipe, RecipeIngredient, Tag)
from rest_framework import serializers
from users.models import MyUser, Subscription


class CreateMyUserSerializer(djoser.serializers.UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class MyUserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с Пользователями."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscription.objects.filter(
                subscriber=request.user, subscriptions=obj
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации об ингредиентах рецепта."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.FloatField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для поля ingredients при создании рецепта"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[MinValueValidator(MIN_AMOUNT)]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = MyUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, required=False, source='recipeingredients'
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, favorites=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Purchase.objects.filter(user=request.user, recipe=obj).exists()
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = AddIngredientSerializer(
        many=True,
        write_only=True,
    )
    author = MyUserSerializer(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'author',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        """Валидация поля tags."""
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег!'
            )
        tag_set = set(tags)
        if len(tags) != len(tag_set):
            raise serializers.ValidationError(
                'Теги не должны повторяться!'
            )

        """ Валидация поля ingredients. """
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент!'
            )
        inrgedients_list = [ingredient['id'] for ingredient in ingredients]
        ingredients_set = set(inrgedients_list)
        if len(ingredients) != len(ingredients_set):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!'
            )
        return data

    @staticmethod
    def create_update_ingredients(ingredients, recipe):
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            amount = ingredient.get('amount')
            RecipeIngredient.objects.update_or_create(
                ingredient=ingredient_id, recipe=recipe, amount=amount
            )

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=request.user)
        recipe.tags.set(tags)
        self.create_update_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.create_update_ingredients(ingredients, instance)
        instance.author = validated_data.get('author', instance.author)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class SimplyRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подписками."""

    email = serializers.CharField(source='subscriptions.email', read_only=True)
    id = serializers.IntegerField(source='subscriptions.id', read_only=True)
    username = serializers.CharField(source='subscriptions.username')
    first_name = serializers.CharField(source='subscriptions.first_name')
    last_name = serializers.CharField(source='subscriptions.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscription.objects.filter(
                subscriber=request.user, subscriptions=obj.subscriptions
            ).exists()
        )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscriptions)
        serializers = SimplyRecipeSerializer(recipes, many=True)
        return serializers.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.subscriptions).count()
