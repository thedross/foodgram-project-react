from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Exists, OuterRef
from colorfield.fields import ColorField

from foodgram.constants import (
    MAX_RECIPES_NAMES_LENGTH,
    MAX_STR_LENGTH,
    MAX_COOCING_VALUE,
    MAX_AMOUNT_VALUE,
    MIN_VALUE,
)
from users.models import FoodgramUser as User


class Tag(models.Model):
    """Класс для модели рецепта."""

    name = models.CharField(
        verbose_name='название тега',
        max_length=MAX_RECIPES_NAMES_LENGTH,
        unique=True
    )
    color = ColorField(
        verbose_name='цвет',
        unique=True
    )
    slug = models.SlugField(
        verbose_name='слаг',
        max_length=MAX_RECIPES_NAMES_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class RecipeQuerySet(models.QuerySet):
    """Класс для аннотирования queryset."""

    def annotate_recipe(self, user_id):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    recipe__pk=OuterRef('pk'),
                    user_id=user_id,
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    recipe__pk=OuterRef('pk'),
                    user_id=user_id,
                )
            ),
        )


class Recipe(models.Model):
    """
    Класс для модели рецепта
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=MAX_RECIPES_NAMES_LENGTH,
        help_text='Введите название рецепта',
    )
    image = models.ImageField(
        verbose_name='картинка',
        upload_to='recipes/images/',
        help_text='загрузите картинку',

    )
    text = models.TextField(
        verbose_name='текст рецепта',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        help_text='выберите ингредиенты для рецепта',
        verbose_name='ингредиенты'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='тег',
        help_text='выберите теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления в минутах',
        help_text='Введите время приготовления в минутах',
        validators=[
            MinValueValidator(
                MIN_VALUE, message='Время готовки не может быть меньше 1!'
            ),
            MaxValueValidator(
                MAX_COOCING_VALUE,
                message='Время готовки не может быть больше 10 ч!'
            )
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True)
    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'

    def __str__(self):
        return f'Рецепт {self.name}. Автор: {self.author.username}'


class Ingredient(models.Model):
    """Класс для модели Ингредиент."""

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=MAX_RECIPES_NAMES_LENGTH,
        help_text='Введите название',
    )
    measurement_unit = models.CharField(
        verbose_name='единица измерения',
        help_text='выберите единицу измерения',
        max_length=MAX_RECIPES_NAMES_LENGTH,
        # Не нужно делать выбор ед.изм.,тк берем их из csv файла
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='Уникальное соответствие названия мере измерения'
            )
        ]

    def __str__(self):
        return f'Ингредиент: {self.name}, измеряется в {self.measurement_unit}'


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи Рецепт - Ингредиент
    """

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='рецепт для ингредиента'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
        verbose_name='ингредиент в рецепте'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество',
        help_text='Введите количество ингредиента',
        validators=[
            MinValueValidator(
                MIN_VALUE, message='Количество не меньше 1!'
            ),
            MaxValueValidator(
                MAX_AMOUNT_VALUE,
                message='Количество не больше 10000!'
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Уникальное соответствие ингредиента рецепту'
            )
        ]

    def __str__(self):
        return (f'В {self.recipe.name} используется {self.ingredient.name}\n'
                f'в количестве {self.amount}'
                f'{self.ingredient.measurement_unit}'
                )


class UserRecipeBaseModel(models.Model):
    """Базовый класс для моделей избранного и корзины."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name="%(class)s",
        related_query_name="%(class)s"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="%(class)s",
        related_query_name="%(class)s",
        verbose_name='Рецепдт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='Уникальное соответствие рецепта пользователю в %(class)s'
            )
        ]


class Favorite(UserRecipeBaseModel):
    """Класс для модели избранного."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self) -> str:
        return f'{self.recipe.name} в избранном {self.user.username}'


class ShoppingCart(UserRecipeBaseModel):
    """Класс для модели Корзины."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'

    def __str__(self):
        return f'{self.recipe.name} в корзине у {self.user.username}'
