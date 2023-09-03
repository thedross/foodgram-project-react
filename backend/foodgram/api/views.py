from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.paginators import CustomPaginationLimit
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    GetRecipeDetailSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for Tag. Only GET method."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # lookup_field = 'id'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for Ingredients"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RecipeViewset(viewsets.ModelViewSet):
    """
    Recipe, Favorite, ShoppingCart.
    Get recipe info. GET.
    Create or update recipe. POST.
    Add or delete from favorite.
    Add or delete from shoppingcart.
    Downloading file with ingredients from shoppingcart.
    """
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter
    pagination_class = CustomPaginationLimit

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe_favorite = Favorite.objects.filter(
            recipe=recipe, user=request.user
        )
        if request.method == 'POST':
            if recipe_favorite.exists():
                return Response(
                    'Рецепт уже в избранном',
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(recipe=recipe, user=request.user)
            return Response(
                RecipeMinifiedSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
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

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe_cart = ShoppingCart.objects.filter(
            recipe=recipe, user=request.user
        )
        if request.method == 'POST':
            if recipe_cart.exists():
                return Response(
                    'Рецепт уже в корзине', status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            return Response(
                RecipeMinifiedSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
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
        """Save shopping cart to file"""
        user = self.request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

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
        file_name = f'{user.username}_shopping_list_ingredients.txt'
        response = HttpResponse(final_to_buy, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file_name}'

        return response

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return GetRecipeDetailSerializer
        return CreateRecipeSerializer
