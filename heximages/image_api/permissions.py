from rest_framework import permissions


class IsImageOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an image to edit it"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsTemporaryLinkOwnerOrReadOnly(permissions.BasePermission):
    """Same permission as above, but for temporary links"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.image.user == request.user


class IsTemporaryLinkCapableOrReadOnly(permissions.BasePermission):
    """Permission to make sure only permitted users can make temporary links"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.image_api_user.tier.can_get_temporary
