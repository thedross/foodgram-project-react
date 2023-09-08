from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.paginators import CustomPaginationLimit
from users.models import FoodgramUser, Follow
from api.serializers import FollowSerializer, FoodgramUserSerializer


class FoodgramUsersViewSet(UserViewSet):
    """
    Вьюсет модели FoodgramUser.
    """

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    filter_backends = (filters.SearchFilter, )
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'id'
    pagination_class = CustomPaginationLimit

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated,],
        serializer_class=FollowSerializer
    )
    def subscribe(self, request, **kwargs):
        # 404 if no author with id given
        following = get_object_or_404(FoodgramUser, id=self.kwargs.get('id'))

        serializer = FollowSerializer(
            following,
            data={'empty': None},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = FollowSerializer(
            following,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        follow = Follow.objects.filter(
            user=request.user,
            following=self.kwargs.get('id')
        )
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
        subscriptions = FoodgramUser.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
