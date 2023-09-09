from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""

    is_in_shopping_cart = filters.BooleanFilter(
        method='method_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(
        method='method_is_favorited')
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        lookup_expr='in'
    )  # In вместо exact по дефолту ищет хотя бы одному совпадению с тегом.

    class Meta:
        model = Recipe
        fields = (
            'is_in_shopping_cart',
            'is_favorited',
            'author',
            'tags'
        )

    def method_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def method_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset


class IngredientsFilter(FilterSet):
    """Фильтр для ингредиентов"""

    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
