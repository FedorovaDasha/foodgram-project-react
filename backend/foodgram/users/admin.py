from django.conf import settings
from django.contrib import admin
from itertools import chain

from .models import MyUser, Subscription


@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'role',
        'first_name',
        'last_name',
        'user_subscriptions',
        'user_favorites',
    )
    list_display_links = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'role')
    empty_value_display = settings.EMPTY_VALUE

    @admin.display(description='Подписки')
    def user_subscriptions(self, object):
        a = object.subscriber.values_list('subscriptions__username')
        return list(chain.from_iterable(a))

    @admin.display(description='Избранное')
    def user_favorites(self, object):
        a = object.favorites.values_list('favorites__name')
        return list(chain.from_iterable(a))


# @admin.register(Subscription)
# class SubscriptionAdmin(admin.ModelAdmin):
#     # list_display = ('id', 'user', 'author')
#     search_fields = ('user', 'author')
#     # list_filter = ('user', 'author')
#     empty_value_display = settings.EMPTY_VALUE
admin.site.register(Subscription)
