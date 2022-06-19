from rest_framework import serializers
from django.contrib.auth.models import User
from image_api.models import Image, ImageAPIUser, TemporaryLink
from rest_framework.reverse import reverse
from datetime import timedelta
from django.utils import timezone


class ThumbnailHyperlink(serializers.HyperlinkedRelatedField):
    """
    Custom class for generating links for thumbnails.
    It's necessary because thumbnails have a custom link structure defined in the ImageViewSet.
    """

    view_name = 'image-thumbnail'

    def get_url(self, obj, view_name, request, format):

        url_kwargs = {
            "name": obj.image.name,
            "height": obj.thumbnail_height.height
        }

        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class ImageDetailHyperlink(serializers.HyperlinkedIdentityField):
    """
    Custom class for generating the link for the original file.
    It's necessary because the link should not be generated if the tier doesn't have that feature
    """

    def get_url(self, obj, view_name, request, format):

        url_kwargs = {
            "name": obj.name
        }

        if obj.user.tier.can_get_temporary:
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        else:
            return ""


class TemporaryLinkHyperlink(serializers.HyperlinkedRelatedField):
    """
    Custom class for generating temporary links.
    It's necessary because the link should not be generated if the tier doesn't have that feature
    """

    def get_url(self, obj, view_name, request, format):

        url_kwargs = {
            "slug": obj.slug
        }

        if obj.image.user.tier.can_get_temporary:
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        else:
            return ""


class ImageSerializer(serializers.HyperlinkedModelSerializer):

    file = serializers.ImageField(write_only=True)
    url = ImageDetailHyperlink(read_only=True, view_name="image-detail")
    user = serializers.ReadOnlyField(source='user.auth_user.username')
    thumbnails = ThumbnailHyperlink(many=True, read_only=True)
    temporary_links = TemporaryLinkHyperlink(many=True, read_only=True, view_name="temporarylink-detail", lookup_field="slug")

    class Meta:
        model = Image
        fields = ['name', 'user', 'file', 'url', 'thumbnails', 'temporary_links']

    def validate_file(self, image):
        """Makes sure the uploaded image is a PNG or a JPEG as required by the project specification"""
        if image.image.format in ('PNG', 'JPEG'):
            return image
        else:
            raise serializers.ValidationError("Image must be a PNG or a JPEG")

    def validate(self, data):
        """
        Makes sure the image name is unique for this user.

        This obviously won't run for Admin forms, but I assume admins won't manually add images,
        and if they do, they will be careful not to use duplicate image names.

        This logic could be easily duplicated in the model's clean method if the client desires so.
        """
        if Image.objects.filter(name=data['name'], user__auth_user=self.context['request'].user).exists():
            raise serializers.ValidationError({"name": "That image already exists!"})
        else:
            return data


class ImageHyperlink(serializers.HyperlinkedRelatedField):

    def get_queryset(self):
        user = self.context["request"].user
        queryset = Image.objects.filter(user__auth_user=user)
        return queryset


class TemporaryLinkSerializer(serializers.HyperlinkedModelSerializer):

    image = ImageHyperlink(view_name='image-detail', lookup_field="name")
    datetime_created = serializers.DateTimeField(read_only=True)
    duration = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="temporarylink-detail", lookup_field="slug")

    class Meta:
        model = TemporaryLink
        fields = ['image', 'datetime_created', 'duration_write', 'duration', 'time_left', 'url']
        extra_kwargs = {'duration_write': {'write_only': True, 'source': 'duration'}}

    def validate_duration(self, duration):
        """Makes sure the duration is compliant with specification"""
        if duration >= timedelta(seconds=300) and duration <= timedelta(seconds=30000):
            return duration
        else:
            raise serializers.ValidationError("Duration must be between 300 and 30000 seconds!")

    def get_duration(self, obj):
        return f"{round(obj.duration.total_seconds())}"

    def get_time_left(self, obj):
        end_time = obj.datetime_created + obj.duration
        time_left = end_time - timezone.now()
        return f"{round(time_left.total_seconds())}"
