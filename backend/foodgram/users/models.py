from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

import foodgram.constants as const
from users.validators import validate_username


class FoodgramUser(AbstractUser):
    '''
    Класс для кастомной модели Юзер для проекта Foodgram.
    Поле email будет использоваться вместо поля username.
    Поле username может быть пустым на этапе создания.
    '''

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        verbose_name='Никнейм',
        max_length=const.MAX_NAME_LENGTH,
        unique=True,
        null=True,
        validators=[
            username_validator,
            validate_username
        ]
    )
    email = models.EmailField(
        verbose_name='e-mail',
        unique=True,
        null=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=const.MAX_NAME_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=const.MAX_NAME_LENGTH,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'last_name', 'first_name')

    class Meta:
        ordering = ('email', 'username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """
    Класс подписки одного пользователя на другого.
    Подписка на самого себя запрещена
    """

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецептов'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_relationships',
                fields=['user', 'following'],
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_prevent_self_follow',
                check=~models.Q(user=models.F('following')),
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} подписан на {self.following.username}'
