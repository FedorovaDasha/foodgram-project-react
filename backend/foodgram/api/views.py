import io
from reportlab.lib.pagesizes import A4, mm
from reportlab.platypus.tables import Table
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets
from djoser.serializers import SetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    Purchase,
    RecipeIngredient
)
from users.models import MyUser, Subscription
from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    ReadRecipeSerializer,
    WriteRecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    MyUserSerializer,
    CreateMyUserSerializer,
    SimplyRecipeSerializer,
    SubscribeSerializer
)

from .permissions import IsAuthorOrAdminOrReadOnly
from .pagination import FoodgramPagination

cm = 2.54


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'DELETE'):
            return WriteRecipeSerializer
        return ReadRecipeSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_name='favorite',
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': 'Невозможно удалить/добавить в избранное несуществующий рецепт!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if not Favorite.objects.filter(user=self.request.user, favorites=pk).exists():
                favorite = Favorite.objects.create(user=self.request.user, favorites=recipe)
                serializer = SimplyRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'errors': 'Рецепт уже есть в избранном!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(favorites=pk, user=self.request.user)
            except Favorite.DoesNotExist:
                return Response(
                    {'errors': 'Рецепт не найден в избранном!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):

        ingredients = RecipeIngredient.objects.filter(
            recipe__purchases_recipe__user=self.request.user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(sum_amount=Sum('amount'))

        buffer = io.BytesIO()
        doc = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        doc.setFont('Arial', 20)
        doc.drawString(220, 770, 'Cписок покупок:')

        width, height = A4
        rows = []
        rows.append(('Ингредиент', 'Количество', 'Единица измерения'))
        ingredients = RecipeIngredient.objects.filter(
            recipe__purchases_recipe__user=self.request.user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(sum_amount=Sum('amount'))
        for ingredient in ingredients:
            rows.append((ingredient['ingredient__name'], ingredient['sum_amount'], ingredient['ingredient__measurement_unit']))
        table = Table(rows, colWidths=65 * mm, rowHeights=25, repeatRows=1)
        table.setStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.darkcyan),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
        ])
        table.wrapOn(doc, width, height)
        table.drawOn(doc, 0 * mm, 5 * mm)
        doc.showPage()
        doc.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='shopping_cart.pdf')

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_name='shopping_cart',
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': 'Невозможно удалить/добавить в список покупок несуществующий рецепт!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if not Purchase.objects.filter(user=self.request.user, recipe=pk).exists():
                purchase = Purchase.objects.create(user=self.request.user, recipe=recipe)
                serializer = SimplyRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'errors': 'Рецепт уже есть в списке покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if request.method == 'DELETE':
            try:
                purchase = Purchase.objects.get(user=self.request.user, recipe=recipe)
            except Purchase.DoesNotExist:
                return Response(
                    {'errors': 'Рецепт не найден в списке покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            purchase.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = MyUser.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = FoodgramPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MyUserSerializer
        return CreateMyUserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """ Метод для получения профиля пользователя. """
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """ Метод для смены пароля пользователя. """
        user = self.request.user
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                'Пароль успешно изменен.', status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_name='subscribe',
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        user = get_object_or_404(MyUser, pk=pk)
        if request.method == 'POST':
            if not Subscription.objects.filter(subscriber=self.request.user, subscriptions=pk).exists():
                subscribe = Subscription.objects.create(subscriber=self.request.user, subscriptions=user)
                serializer = SubscribeSerializer(subscribe, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'errors': 'Ошибка подписки!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if request.method == 'DELETE':
            try:
                subscribe = Subscription.objects.get(subscriber=self.request.user, subscriptions=pk)
            except Subscription.DoesNotExist:
                return Response(
                    {'errors': 'Ошибка отписки!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_name='subscriptions',
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(subscriber=self.request.user)
        limit_pages = self.paginate_queryset(subscriptions)
        serializer = SubscribeSerializer(limit_pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
