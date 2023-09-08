from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'image'
    )
    search_fields = (
        'email',
        'first_name',
        'last_name'
    )
    inlines = (RecipeIngredientsInLine,)
    ordering = ('name',)
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('recipe_is_favorite',)

    @admin.display(description='Рецепт в избранном')
    def recipe_is_favorite(self, obj):
        # Count new field
        return obj.favorite.count()

    @admin.display(description='картинка')
    def image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">')


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


admin.site.unregister(Group)
