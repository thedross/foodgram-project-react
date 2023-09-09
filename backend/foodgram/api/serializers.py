# api.serializers
# Все сериализаторы
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from foodgram.constants import MAX_AMOUNT_VALUE, MIN_VALUE, MAX_COOCING_VALUE

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User
)
from users.models import Follow


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор модели FoodgramUser."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.follower.filter(
                    user=user,
                    following=obj
                ).exists())


class FollowSerializer(FoodgramUserSerializer):
    """
    Сериализатор для подписок. На основе FoodgramUserSerializer.
    Возвращает 400 при попытке подписаться на себя,
    и если подписка уже существует.
    Два новых поля:
    recipes, recipes_count.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(FoodgramUserSerializer.Meta):
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count')

    def get_recipes(self, obj):
        """Получение краткой информации о рецептах."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            # Cut to amount of recipes according to limit
            recipes = recipes[:int(recipes_limit)]

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            read_only=True
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowModelSerializer(serializers.ModelSerializer):
    """Сериализатор для модели подписки."""

    class Meta:
        model = Follow

    def validate(self, data):
        """Валидирует самоподписку либо если подписка существует"""
        user = self.context.get('request').user
        if self.instance == user:
            raise serializers.ValidationError(
                detail='Нельзя подписаться на себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(following=self.instance, user=user).exists():
            raise serializers.ValidationError(
                detail={'error': 'Подписка существует.'},
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        return FollowSerializer(instance, context=self.context).data


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
                  'cooking_time',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингрединет."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAddToRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингредиент для добавления в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            write_only=True)
    amount = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_AMOUNT_VALUE
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.
    """

    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientAddToRecipeSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_COOCING_VALUE
    )
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

    def validate(self, data):
        if not data.get('ingredients'):
            raise serializers.ValidationError('Добавьте хотя бы 1 ингредиент')
        ingredients = [ingredient['id'] for ingredient in data['ingredients']]
        # Need to use key because OrderedDict is not hashable
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться'
            )
        return data

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Add at least one tag!')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Tags can\'t repeat!')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Need to add an image!')
        return value

    @staticmethod
    def save_ingredients(recipe, ingredients):
        """Отдельная функция для сохранения ингредиентов."""
        ingredients_list = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
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
        return GetRecipeDetailSerializer(instance, context=self.context).data


class IngredientsDetailForRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения информации ингредиента в рецепте.
    """

    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        read_only=True,
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        read_only=True,
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class GetRecipeDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения подробной информации рецепта.
    """

    tags = TagSerializer(many=True, read_only=True)
    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientsDetailForRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredient'
    )
    image = Base64ImageField()
    is_favorited = serializers.IntegerField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

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


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине.'
            )
        ]

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            )
        ]

    def to_representation(self, instance):
        return GetRecipeDetailSerializer(
            instance.recipe, context=self.context
        ).data
