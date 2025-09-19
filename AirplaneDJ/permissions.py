from rest_framework.permissions import BasePermission, SAFE_METHODS

def is_admin(user):
    return user.is_authenticated and (user.is_staff or getattr(user, 'role', None) == 'admin')

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
        request.user and request.user.is_authenticated and (
        request.user.is_staff or getattr(request.user, 'role', None) == 'admin'
            )
        )

class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
        obj == request.user or
            (request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user, 'role', None) == 'admin'))
)


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS