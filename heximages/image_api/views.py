from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from image_api.models import Image, ThumbnailHeight
from image_api.serializers import ImageSerializer
from rest_framework import permissions
from image_api.permissions import IsOwnerOrReadOnly
from pathlib import Path


class ImageViewSet(viewsets.ModelViewSet):

    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'name'

    def retrieve(self, request, name, *args, **kwargs):
        image = self.get_object()
        content_type = "image/png" if Path(image.file.path).suffix == "png" else "image/jpeg"
        response = Response(content_type=content_type)
        response['X-Accel-Redirect'] = image.file.url
        return response

    @action(detail=True, url_path=r'thumbnail/(?P<height>[\d]+)')
    def thumbnail(self, request, height, *args, **kwargs):
        image = self.get_object()
        thumbnail_height = ThumbnailHeight.objects.get(height=height)
        thumbnail = image.thumbnails.get(thumbnail_height=thumbnail_height)
        content_type = "image/png" if Path(thumbnail.file.path).suffix == "png" else "image/jpeg"
        response = Response(content_type=content_type)
        response['X-Accel-Redirect'] = thumbnail.file.url
        return response

    def get_queryset(self):
        print("get queryset runs")
        user = self.request.user.image_api_user
        return Image.objects.filter(user=user)

    def perform_create(self, serializer):
        print("perform create runs")
        serializer.save(user=self.request.user.image_api_user)
