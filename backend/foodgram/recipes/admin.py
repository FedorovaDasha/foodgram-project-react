from django.contrib import admin
from django.utils.safestring import mark_safe
from itertools import chain

from .models import (
    Tag,
    Recipe,
    Ingredient,
    RecipeIngredient,
    Favorite,
    Purchase,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    inlines = (
        RecipeIngredientInline,
    )

    list_display = (
        'author',
        'name',
        'preview',
        'tags_names',
        'text',
        'ingredients_names',
        'cooking_time',
        'count_favorite'
    )
    search_fields = ('name',)
    list_filter = (
        'tags',
        'name',
        'author',
    )
    list_display_links = ('name',)
    readonly_fields = ('preview',)

    @admin.display(description="В избранном", empty_value="Нет в избранном")
    def count_favorite(self, object):
        count = object.favorites.count()
        if count:
            return count

    @admin.display(description='Ингредиенты')
    def ingredients_names(self, object):
        ingredients = object.ingredients.values_list('name')
        return list(chain.from_iterable(ingredients))

    @admin.display(description='Теги')
    def tags_names(self, object):
        tags = object.tags.values_list('name')
        return list(chain.from_iterable(tags))

    @admin.display(description='Фото рецепта', empty_value='Нет фото')
    def preview(self, object):
        if object.image:
            return mark_safe(
                f'<img src="{object.image.url}" '
                'style="max-height: 100px; max-width: 100px">'
            )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


admin.site.register(Purchase)
admin.site.register(Favorite)
