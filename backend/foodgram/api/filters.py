from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tag
User = get_user_model()


class RecipeFilter(FilterSet):
    """Filter for Recipe"""
    is_in_shopping_cart = filters.BooleanFilter(
        method='method_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(
        method='method_is_favorited')
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

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
            return queryset.filter(cart__user=self.request.user)
        return queryset
