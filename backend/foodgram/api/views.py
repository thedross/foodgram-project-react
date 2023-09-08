import tempfile

from django.db.models import F, Sum
from django.http import FileResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientsFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    GetRecipeDetailSerializer,
    IngredientSerializer,
    # RecipeMinifiedSerializer,
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

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'ingredients',
        'tags'
    )
    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter

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

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        self.favorite_or_cart_save(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        """
        Потрясающе. mapping.delete для декорирования запросов
        на удаление подписки.
        """
        recipe_favorite = Favorite.objects.filter(user=request.user, recipe=pk)
        if recipe_favorite.exists():
            recipe_favorite.delete()
            return Response(
                'Рецепт удален из избранного',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            'Рецепта нет в избранном',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['POST'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        self.favorite_or_cart_save(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        recipe_cart = ShoppingCart.objects.filter(user=request.user, recipe=pk)
        if recipe_cart.exists():
            recipe_cart.delete()
            return Response(
                'Рецепт удален из корзины',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            'Рецепта нет в корзине',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['GET'],
            permission_classes=[permissions.IsAuthenticated],
            detail=False)
    def download_shopping_cart(self, request):
        """Подготовка queryset и вызов функции на скачивание."""
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by('name')

        self.making_file_with_ingredients(user, ingredients)

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
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            # Записываем во временный файл
            temp_file.write(final_to_buy.encode())
            temp_file.seek(0)
        response = FileResponse(temp_file, content_type='text/plain')
        filename = f'{user.username}_shopping_list_ingredients.txt'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return GetRecipeDetailSerializer
        return CreateRecipeSerializer
