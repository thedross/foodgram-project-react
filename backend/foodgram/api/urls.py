from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewset, TagViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredient'
    )
router.register(r'recipes', RecipeViewset, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
]
