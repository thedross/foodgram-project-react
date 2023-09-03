from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from djoser.serializers import UserSerializer, UserCreateSerializer
# from rest_framework.validators import UniqueTogetherValidator
from api.serializers import RecipeMinifiedSerializer
from users.models import Follow

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    """
    Сериализатор модели FoodgramUser.
    """
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
                and Follow.objects.filter(
                    user=user,
                    following=obj
                ).exists()
                )


class FoodgramCreateUserSerializer(UserCreateSerializer):
    """
    Сериализатор модели User для регистрации.
    """
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        """
        Если пользователь с таким email уже существует,
        новый пользователь не создастся.
        """
        email = data.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email уже существует.'}
            )
        return data

    def create(self, validated_data):
        """
        Create user, saves password in hash
        """
        user, created = User.objects.get_or_create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        if created:
            return user
        return validated_data


class FollowSerializer(FoodgramUserSerializer):
    """
    Serializer for follow/unfollow and getting follow.
    Based on FoodgramUserSerializer.
    400 - Prevents selffollow and if model exists.
    Add two new atrributes: recipes and recipes_count.
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
                  'recipes_count'
                  )

    def validate(self, data):
        """
        Validate to prevent selffollow.
        Prevents creating existing object.
        """
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

    def get_recipes(self, obj):
        """
        Getting short info recipes.
        Use RecipeMinifiedSerializer.

        """
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit:
            # Cut to amount of recipes according to limit
            recipes = recipes[:int(recipes_limit)]

        serializer = RecipeMinifiedSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
