from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import FoodgramUsersViewSet

router = DefaultRouter()
router.register('users', FoodgramUsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
