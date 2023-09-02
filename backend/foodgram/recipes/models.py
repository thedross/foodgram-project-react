from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name='название тега',
        max_length=150,
        unique=True
    )
    color = models.CharField(
        verbose_name='цвет',
        max_length=150,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='слаг',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Recipe(models.Model):
    '''
    Класс для модели рецепта
    '''
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=150,
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
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='тег',
        help_text='выберите теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления в минутах',
        help_text='Введите время приготовления в минутах',
        validators=[MinValueValidator(1)],  # исправить магическое число
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']
        default_related_name = 'recipes'

    def __str__(self):
        return f'Рецепт {self.name}. Автор: {self.author.username}'


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=200,  # убрать магическое число
        help_text='Введите название',
    )
    measurement_unit = models.CharField(
        verbose_name='единица измерения',
        help_text='выберите единицу измерения',
        max_length=150,
        # Не нужно делать выбор ед.изм.,тк берем их из csv файла
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class RecipeIngredient(models.Model):
    '''
    Промежуточная модель для связи Рецепт - Ингредиент
    '''
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество',
        help_text='Введите количество ингредиента',
        validators=[MinValueValidator(
            limit_value=1,  # убрать магическое число
            message='Количество ингредиента не может быть меньше 1'
            )
        ]
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


class Favorite(models.Model):
    '''Model adding recipe to favorites'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепдт',
        related_name='favorite',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='Уникальное соответствие избранного рецепта пользователю'
            )
        ]

    def __str__(self) -> str:
        return f'{self.recipe.name} в избранном {self.user.username}'


class ShoppingCart(models.Model):
    """Class for shopping cart."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='cart',
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='Уникальное соответствие рецепта в корзине к пользователю'
            )
        ]

    def __str__(self) -> str:
        return f'{self.recipe.name} в корзине у {self.user.username}'
