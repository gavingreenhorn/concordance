from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.id == obj.author.id)