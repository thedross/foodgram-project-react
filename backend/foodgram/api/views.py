import tempfile

from djoser.views import UserViewSet
from django.db.models import F, Sum
from django.http import FileResponse
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientsFilter, RecipeFilter
from api.paginators import CustomPaginationLimit
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    FoodgramUserSerializer,
    FollowModelSerializer,
    FollowSerializer,
    GetRecipeDetailSerializer,
    IngredientSerializer,
    ShoppingCartSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import FoodgramUser, Follow


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Тег"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Ингредиент"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientsFilter


class RecipeViewset(viewsets.ModelViewSet):
    """
    Класс для работы с рецептами.
    Добавлению в избранное и корзину.
    Скачивание ингредиентов из корзины.
    Остальные действия с рецептами.
    """

    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Самый длинный запрос в жизни."""
        user_id = self.request.user.pk
        queryset = Recipe.objects.annotate_recipe(
            user_id
        ).select_related(
            'author'
        ).prefetch_related(
            'ingredients',
            'tags'
        )

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer
        return GetRecipeDetailSerializer

    @staticmethod
    def favorite_or_cart_save(request, pk, serializer_choice):
        user = request.user
        data = {'user': user.id, 'recipe': pk}
        serializer = serializer_choice(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def favorite_or_cart_delete(request, pk, model):
        recipe_user = model.objects.filter(user=request.user, recipe=pk)
        if recipe_user.exists():
            recipe_user.delete()
            return Response(
                'Связь рецепт-пользователь удалена.',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            'Свзяь рецепт-пользователь не найдена.',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.favorite_or_cart_save(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        """
        Потрясающе. mapping.delete для декорирования запросов
        на удаление подписки.
        """
        return self.favorite_or_cart_delete(request, pk, Favorite)

    @action(methods=['POST'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self.favorite_or_cart_save(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        return self.favorite_or_cart_delete(request, pk, ShoppingCart)

    @action(methods=['GET'],
            permission_classes=[permissions.IsAuthenticated],
            detail=False)
    def download_shopping_cart(self, request):
        """Подготовка queryset и вызов функции на скачивание."""
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by('name')

        return self.making_file_with_ingredients(user, ingredients)

    @staticmethod
    def making_file_with_ingredients(user, ingredients):
        """Создаем и скачиваем файл с ингредиентами."""
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(
                f'{ingredient["name"]} --> '
                f'{ingredient["amount"]} '
                f'({ingredient["measurement_unit"]})'
            )

        final_to_buy = ('Ваш список ингредиентов для '
                        'создания всех рецептов из корзины.\n\n')
        final_to_buy += '\n'.join(ingredients_list)
        with tempfile.NamedTemporaryFile(
            delete=True, encoding='utf-8'
        ) as temp_file:
            # Записываем во временный файл
            temp_file.write(final_to_buy.encode())
            temp_file.seek(0)
            return FileResponse(
                temp_file,
                as_attachment=True,
                filename=f'{user.username}_shopping_list_ingredients.txt',
                content_type='text/plain'
            )


class FoodgramUsersViewSet(UserViewSet):
    """
    Вьюсет модели FoodgramUser.
    """

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    filter_backends = (filters.SearchFilter, )
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'id'
    pagination_class = CustomPaginationLimit

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated, ],
        serializer_class=FollowSerializer
    )
    def subscribe(self, request, **kwargs):

        following = FoodgramUser.objects.get(id=self.kwargs.get('id'))

        serializer = FollowModelSerializer(
            following,
            data={'empty': None},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        follow = Follow.objects.filter(
            user=request.user,
            following=self.kwargs.get('id')
        )
        if not follow.exists():
            return Response(
                'Нельзя отписаться, так как вы не подписаны',
                status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(
            'Успешно отписались',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(methods=['GET'],
            detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        """
        Method to get subscriprions.
        Uses FollowSerializer. Can take arguments: limit, recipes_limit
        """
        user = request.user
        subscriptions = FoodgramUser.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
