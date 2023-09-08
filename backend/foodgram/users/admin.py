from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser, Follow


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    search_fields = (
        'email',
        'first_name',
        'last_name'
    )
    ordering = ('email',)
    list_filter = ('email', 'username',)

    @admin.display(description='Рецепты')
    def recipes(self, obj):
        # Count new field
        recipes = obj.recipes.all()
        return ', '.join([recipe.name for recipe in recipes])


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'following',
    )
