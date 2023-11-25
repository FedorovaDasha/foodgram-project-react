import django_filters
from django.db import models

from recipes.models import Ingredient, Recipe
from users.models import MyUser


class IngredientNameFilter(django_filters.Filter):
    def filter(self, queryset, value):
        if value:
            queryset_1 = queryset.filter(name__istartswith=value).annotate(
                qs_order=models.Value(1, models.IntegerField())
            )
            queryset_2 = queryset.filter(name__icontains=value).exclude(
                name__istartswith=value
            ).annotate(qs_order=models.Value(2, models.IntegerField()))
            union_qs = queryset_1.union(queryset_2).order_by('qs_order')

        return union_qs


class IngredientFilter(django_filters.FilterSet):

    name = IngredientNameFilter()

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        to_field_name='id',
        queryset=MyUser.objects.all()
    )
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart',)

    def filter_is_favorited(self, queryset, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, value):
        if value:
            return queryset.filter(
                purchases_recipe__user=self.request.user)
        return queryset
