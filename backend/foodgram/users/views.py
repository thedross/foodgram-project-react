from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from api.paginators import CustomPaginationLimit
from users.models import Follow
from users.serializers import FollowSerializer, FoodgramUserSerializer


User = get_user_model()


class FoodgramUsersViewSet(UserViewSet):
    """
    Вьюсет модели FoodgramUser.
    """
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    filter_backends = (filters.SearchFilter, )
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'
    pagination_class = CustomPaginationLimit

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[permissions.IsAuthenticated, ]
    )
    def me(self, request, *args, **kwargs):
        return Response(FoodgramUserSerializer(
            request.user,
            context={'request': request}
            ).data
        )

    @action(
            detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[permissions.IsAuthenticated, ]
    )
    def subscribe(self, request, **kwargs):
        user = self.request.user
        # 404 if no author with id given
        following = get_object_or_404(User, id=self.kwargs.get('id'))
        if request.method == 'POST':
            serializer = FollowSerializer(
                following,
                data={'empty': None},
                context={'request': request}
                )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=following)

            serializer = FollowSerializer(
                following,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, following=following)
            if not follow.exists():
                return Response(
                    'Нельзя отписаться, так как вы не подписаны',
                    status=status.HTTP_400_BAD_REQUEST
                    )
            follow.delete()
            return Response(
                'Успешно отписались',
                status=status.HTTP_204_NO_CONTENT
            )

    @action(methods=['GET'],
            detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        """
        Method to get subscriprions.
        Uses FollowSerializer. Can take arguments: limit, recipes_limit
        """
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
