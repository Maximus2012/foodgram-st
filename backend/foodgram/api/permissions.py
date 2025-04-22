from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешить доступ только владельцу объекта или только для чтения остальным."""

    def has_object_permission(self, request, view, obj):
        # Разрешаем доступ для чтения всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем доступ для изменения объекта только владельцу
        return obj.author == request.user  # Проверяем, что автор объекта — это текущий пользователь