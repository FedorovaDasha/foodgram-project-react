from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from recipes.models import (Favorite, Ingredient, Purchase, Recipe,
                            RecipeIngredient, Tag)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus.tables import Table
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import MyUser, Subscription

from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (CreateMyUserSerializer, IngredientSerializer,
                          MyUserSerializer, ReadRecipeSerializer,
                          SimplyRecipeSerializer, SubscribeSerializer,
                          TagSerializer, WriteRecipeSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = Recipe.custom_objects.add_user_annotations(
                self.request.user.id
            )
        else:
            queryset = Recipe.custom_objects.all_recipes()

        if (
            'is_favorited' in self.request.query_params
            and self.request.user.is_authenticated
        ):
            queryset = queryset.filter(is_favorited=True)

        if (
            'is_in_shopping_cart' in self.request.query_params
            and self.request.user.is_authenticated
        ):
            queryset = queryset.filter(is_in_shopping_cart=True)

        return queryset

    def get_serializer_class(self):
        """Метод  для определения класса сериализатора."""

        if self.request.method in ('POST', 'PATCH', 'DELETE'):
            return WriteRecipeSerializer
        return ReadRecipeSerializer

    def add_method(self, model, recipe, args):
        """Метод  для добавления в избранное или список покупок."""

        if model.objects.filter(**args).exists():
            return Response(
                {'errors': 'Рецепт уже есть в избранном/списке покупок!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(**args)
        serializer = SimplyRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_method(self, model, args):
        """Метод  для удаления из избранного или списка покупок."""

        if not (obj := model.objects.filter(**args).first()):
            return Response(
                {'errors': 'Рецепт не найден в избранном/списке покупок!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_recipe(pk):
        """Метод возвращает рецепт по pk."""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': 'Операция с несуществующим рецептом невозможна!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return recipe

    @action(
        detail=True,
        methods=['POST'],
        url_name='favorite',
        url_path='favorite',
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk):
        """Метод  для добавления рецепта в избранное."""

        recipe = self.get_recipe(pk)
        args = {'user': self.request.user, 'favorites': recipe}
        return self.add_method(Favorite, recipe, args)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Метод  для удаления рецепта из избранного."""

        recipe = self.get_recipe(pk)
        args = {'user': self.request.user, 'favorites': recipe}
        return self.delete_method(Favorite, args)

    @action(
        detail=True,
        methods=['POST'],
        url_name='shopping_cart',
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        """Метод  для добавления рецепта в список покупок."""

        recipe = self.get_recipe(pk)
        args = {'user': self.request.user, 'recipe': recipe}
        return self.add_method(Purchase, recipe, args)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Метод  для удаления рецепта из списка покупок."""

        recipe = self.get_recipe(pk)
        args = {'user': self.request.user, 'recipe': recipe}
        return self.delete_method(Purchase, args)

    @staticmethod
    def generate_pdf(pdf, ingredients):
        """Метод, генерирующий pdf-файл."""

        pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf'))
        pdfmetrics.registerFont(
            TTFont('DejaVuSerifBold', 'DejaVuSerif-Bold.ttf')
        )
        doc_obj = []
        style = ParagraphStyle(
            name='Normal',
            fontName='DejaVuSerifBold',
            fontSize=15,
            spaceAfter=14,
            spaceBefore=20,
        )
        doc_obj.append(Paragraph('Список покупок:', style=style))
        rows = []
        rows.append(('Ингредиент', 'Количество', 'Ед.измерения'))
        for ingredient in ingredients:
            rows.append(
                (
                    ingredient['ingredient__name'],
                    ingredient['sum_amount'],
                    ingredient['ingredient__measurement_unit'],
                )
            )
        table = Table(
            rows,
            colWidths=[340, 100, 100],
            rowHeights=20,
        )
        table.setStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.5, colors.darkcyan),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ]
        )
        doc_obj.append(table)
        pdf.build(doc_obj)
        return pdf

    @action(
        detail=False,
        methods=['GET'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Метод  для формирования списка покупок в pdf-файле."""

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__purchases_recipe__user=self.request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(sum_amount=Sum('amount'))
        )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="purchase.pdf"'
        pdf = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=15,
            bottomMargin=15,
        )
        self.generate_pdf(pdf, ingredients)
        return response


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = MyUser.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = FoodgramPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MyUserSerializer
        return CreateMyUserSerializer

    @action(
        detail=False, methods=['GET'], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Метод для получения профиля пользователя."""
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False, methods=['POST'], permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Метод для смены пароля пользователя."""
        user = self.request.user
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            'Пароль успешно изменен.', status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['POST'],
        url_name='subscribe',
        url_path='subscribe',
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
        """Метод  для работы с подписками пользователя."""

        user = get_object_or_404(MyUser, pk=pk)
        if Subscription.objects.filter(
            subscriber=self.request.user, subscriptions=pk
        ).exists():
            return Response(
                {'errors': 'Ошибка подписки!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscribe = Subscription.objects.create(
            subscriber=self.request.user, subscriptions=user
        )
        serializer = SubscribeSerializer(
            subscribe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        get_object_or_404(MyUser, pk=pk)
        if not (
            subscribe := Subscription.objects.filter(
                subscriber=self.request.user, subscriptions=pk
            ).first()
        ):
            return Response(
                {'errors': 'Ошибка отписки!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_name='subscriptions',
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """Подписки пользователя."""

        subscriptions = Subscription.objects.filter(
            subscriber=self.request.user
        )
        limit_pages = self.paginate_queryset(subscriptions)
        serializer = SubscribeSerializer(
            limit_pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
