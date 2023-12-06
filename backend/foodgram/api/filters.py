import django_filters
from django.db.models import Case, Q, Value, When
from recipes.models import Ingredient, Recipe
from users.models import MyUser


class IngredientNameFilter(django_filters.Filter):
    def filter(self, queryset, value):
        if value:
            queryset = queryset.filter(name__icontains=value).annotate(
                qs_order=Case(
                    When(Q(name__istartswith=value), then=Value('1')),
                    default=Value('2')
                )
            ).order_by('qs_order', 'name')
        return queryset


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
    is_favorited = django_filters.BooleanFilter(
        field_name='is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )
