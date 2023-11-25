from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    '''Доступ администратора или суперпользователя,
       для остальных - только для чтения.'''
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdmin(BasePermission):
    '''Доступ администратора или суперпользователя.'''

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """
    Неавторизованным пользователям разрешён только просмотр.
    Если пользователь является администратором
    или владельцем записи, то возможны остальные методы.
    """
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (obj.author == request.user
                or request.user.is_superuser)


class IsCurrentUserOrAdminOrReadOnly(BasePermission):
    """
    Неавторизованным пользователям разрешён только просмотр.
    Если пользователь является администратором
    или пользователем, то возможны остальные методы.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (obj.id == request.user
                or request.user.is_superuser)
