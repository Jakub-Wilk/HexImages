from rest_framework import serializers
from django.contrib.auth.models import User
from image_api.models import Image, ImageAPIUser
from rest_framework.reverse import reverse


class ThumbnailHyperlink(serializers.HyperlinkedRelatedField):

    view_name = 'image-thumbnail'

    def get_url(self, obj, view_name, request, format):
        print("get url runs")

        url_kwargs = {
            "name": obj.image.name,
            "height": obj.thumbnail_height.height
        }

        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class ImageHyperlink(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):

        url_kwargs = {
            "name": obj.name
        }

        if obj.user.tier.can_get_original:
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        else:
            return ""


class ImageSerializer(serializers.HyperlinkedModelSerializer):

    file = serializers.ImageField(write_only=True)
    url = ImageHyperlink(read_only=True, view_name="image-detail")
    user = serializers.ReadOnlyField(source='user.auth_user.username')
    thumbnails = ThumbnailHyperlink(many=True, read_only=True)

    class Meta:
        model = Image
        fields = ['name', 'user', 'file', 'url', 'thumbnails']

    def validate_file(self, image):
        print("file validator runs")
        if image.image.format in ('PNG', 'JPEG'):
            print("format correct")
            return image
        else:
            print("format incorrect")
            raise serializers.ValidationError("Image must be a PNG or a JPEG")

    def validate(self, data):
        print("name validator runs")
        if Image.objects.filter(name=data['name'], user__auth_user=self.context['request'].user).exists():
            raise serializers.ValidationError({"name": "That image already exists!"})
        else:
            return data

    def get_url(self, image):
        request = self.context.get('request')
        if image.user.tier.can_get_original:
            return request.build_absolute_uri(image.file.url)
        else:
            return ''
