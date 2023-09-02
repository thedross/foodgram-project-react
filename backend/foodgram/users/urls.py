from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import FoodgramUsersViewSet
# from djoser import views
router = DefaultRouter()
router.register('users', FoodgramUsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
