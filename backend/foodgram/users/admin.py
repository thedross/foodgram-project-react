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
        'recipes',
        'followers'
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
        return ', '.join([recipe.name for recipe in obj.recipes.all()])

    @admin.display(description='Количество подписчиков')
    def followers(self, obj):
        return obj.following.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'following',
    )
