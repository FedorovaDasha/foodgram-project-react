from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    IngredientViewSet,
    TagViewSet,
    UserViewSet
)
# from users.views import (
#     FavoriteViewSet,
#     SubscriptionViewSet,
#     PurchaseViewSet,
# )
app_name = 'api'

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', UserViewSet, basename='users')
# router.register(
#     r'v1/posts/(?P<post_id>\d+)/comments',
#     CommentViewSet, basename='comments'
# )

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
