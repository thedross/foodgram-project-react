# api.serializers
# Все сериализаторы, кроме User и Follow
import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.serializers import UserSerializer


class Base64ImageField(serializers.ImageField):
    """
    Сериализатор для декодирования картинки рецепта из base64.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)
        return super().to_internal_value(data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения краткой информации рецептов.
    Используется при подписке, и получении списка подписок на пользователей.
    Для представлений Подписок, Корзины, Избранного.
    """
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time',
                  )


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Tag.
    """
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for Ingredient Model.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAddToRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Ингредиент для добавления в рецепт.
    """
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.
    """
    author = UserSerializer(read_only=True)
    ingredients = IngredientAddToRecipeSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Add at least one ingredient'
            )
        print('>>>>>>>', value)
        ingredients = [ingredient['id'] for ingredient in value]
        # Need to use key because OrderedDict is not hashable
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ingredients can\'t repeat'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Add at least one tag')
        return value

    def save_ingredients(self, recipe, ingredients):
        """Separate function because 2 times needed."""
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(RecipeIngredient(
                recipe=recipe,
                ingredient=get_object_or_404(
                    Ingredient,
                    pk=ingredient.get('id')
                ),
                amount=ingredient.get('amount')
            ))
        RecipeIngredient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.save_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipeDetailSerializer(instance, context=context).data


class IngredientsDetailForRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения информации ингредиента в рецепте.
    """
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_amount(self, obj):
        return obj.amount


class GetRecipeDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения подробной информации рецепта.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

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

    def get_ingredients(self, obj):
        '''
        Get list of ingredients from RecipeIngredient.
        After gets full information for each ingredient.
        '''
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientsDetailForRecipeSerializer(
            ingredients,
            many=True
        ).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.favorite.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.cart.filter(recipe=obj).exists()
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for model ShoppingCart"""
    class Meta:
        model = ShoppingCart
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине.'
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for model Favorite"""
    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            )
        ]
