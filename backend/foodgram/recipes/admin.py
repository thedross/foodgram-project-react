from django.contrib import admin
from django.contrib.admin import ModelAdmin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    search_fields = (
        'email',
        'first_name',
        'last_name'
    )
    ordering = ('name',)
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('recipe_is_favorite',)

    def recipe_is_favorite(self, obj):
        # Count new field
        return obj.favorite.count()
    recipe_is_favorite.short_description = 'Рецепт в избранном'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount'
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
