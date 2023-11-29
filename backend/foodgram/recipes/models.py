from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

MIN_COOKING_TIME = 1
MIN_AMOUNT = 1

User = get_user_model()


class Tag(models.Model):
    """ Модель тегов. """

    name = models.CharField(max_length=200, verbose_name='Название тега')
    color = models.CharField(max_length=7, verbose_name='Цвет тега')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингредиентов. """
    
    name = models.CharField(
        max_length=200,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_Ingredient_measurement_unit'
            )
        ]
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """ Модель рецептов. """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото рецепта',
        default=None,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги рецепта'
    )
    cooking_time = models.SmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Время приготовления'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Модель, для реализации связи рецептов и ингредиентов. """

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipeingredients',
        on_delete=models.CASCADE
    )
    amount = models.SmallIntegerField(
        validators=[MinValueValidator(MIN_AMOUNT)],
        verbose_name='Количество',
        )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self) -> str:
        return f'{self.ingredient}, {self.amount}'


class Favorite(models.Model):
    """ Модель избранного. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    favorites = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранное'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'favorites'],
                name='unique_user_favorites'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.favorites} в избранном у {self.user}'


class Purchase(models.Model):
    """ Модель для списка рецептов. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='purchases_recipe',
        verbose_name='Список покупок',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_purchase'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.recipe} в списке покупок у {self.user}'
