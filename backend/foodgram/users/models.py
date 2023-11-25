from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class MyUser(AbstractUser):
    """Класс пользователей."""

    ADMIN = 'admin'
    USER = 'user'
    ROLE_CHOICES = (
        (ADMIN, 'Администратор'),
        (USER, 'Пользователь'),
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    username = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя',
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Недопустимые символы для имени пользователя'),
        ]
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Email',
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    role = models.CharField(
        max_length=20,
        verbose_name='Роль пользователя',
        choices=ROLE_CHOICES,
        default=USER
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser or self.is_staff


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    subscriptions = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписки'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscriptions'],
                name='unique_user_subscriptions'
            ),
            models.CheckConstraint(
                check=~Q(subscriber__exact=F('subscriptions')),
                name='check_subscribe_to_yourself',
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscriptions}'
