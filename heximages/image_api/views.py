from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from image_api.models import Image, TemporaryLink, ThumbnailHeight
from image_api.serializers import ImageSerializer, TemporaryLinkSerializer
from rest_framework import permissions
from image_api.permissions import IsImageOwnerOrReadOnly, IsTemporaryLinkCapableOrReadOnly, IsTemporaryLinkOwnerOrReadOnly
from pathlib import Path
from django.utils import timezone
from django.db.models import F


class ImageViewSet(viewsets.ModelViewSet):

    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsImageOwnerOrReadOnly]
    lookup_field = 'name'

    def retrieve(self, request, name, *args, **kwargs):
        image = self.get_object()
        content_type = "image/png" if Path(image.file.path).suffix == "png" else "image/jpeg"
        response = Response(content_type=content_type)
        response['X-Accel-Redirect'] = image.file.url  # X-Accel-Redirect is used to serve the asset behind the scenes using NGINX
        return response

    @action(detail=True, url_path=r'thumbnail/(?P<height>[\d]+)')
    def thumbnail(self, request, height, *args, **kwargs):
        """
        A custom action to not write a separate view for thumbnails,
        as they are an unseparable part of their image, and should be viewed as such
        """
        image = self.get_object()
        thumbnail_height = ThumbnailHeight.objects.get(height=height)
        thumbnail = image.thumbnails.get(thumbnail_height=thumbnail_height)
        content_type = "image/jpeg"  # thumbnails are always JPEG
        response = Response(content_type=content_type)
        response['X-Accel-Redirect'] = thumbnail.file.url  # X-Accel-Redirect is used to serve the asset behind the scenes using NGINX
        return response

    def get_queryset(self):
        user = self.request.user.image_api_user

        # dirty hack to make sure outdated links are deleted
        # this has to be placed in the get_queryset of every
        # ViewSet that includes temporary links
        # I couldn't find a proper way to do it, but this works
        outdated_links = TemporaryLink.objects.filter(datetime_created__lte=timezone.now() - F("duration"))
        outdated_links.delete()

        queryset = Image.objects.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.image_api_user)


class TemporaryLinkViewSet(viewsets.ModelViewSet):

    serializer_class = TemporaryLinkSerializer
    permission_classes = [permissions.IsAuthenticated, IsTemporaryLinkOwnerOrReadOnly, IsTemporaryLinkCapableOrReadOnly]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        temporary_link = self.get_object()
        content_type = "image/png" if Path(temporary_link.image.file.path).suffix == "png" else "image/jpeg"
        response = Response(content_type=content_type)
        response['X-Accel-Redirect'] = temporary_link.image.file.url  # X-Accel-Redirect is used to serve the asset behind the scenes using NGINX
        return response

    def get_queryset(self):
        user = self.request.user.image_api_user
        outdated_links = TemporaryLink.objects.filter(datetime_created__lte=timezone.now() - F("duration"))
        outdated_links.delete()
        queryset = TemporaryLink.objects.filter(image__user=user)
        return queryset
