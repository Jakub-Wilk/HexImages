from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class ThumbnailResolution(models.Model):
    height = models.IntegerField(validators=[MinValueValidator(0)])


class Tier(models.Model):
    name = models.CharField()
    resolutions = models.ManyToManyField(ThumbnailResolution)
    can_get_original = models.BooleanField(default=False)
    can_get_temporary = models.BooleanField(default=False)


class ImageAPIUser(models.Model):
    user = models.OneToOneField(User, related_name="image_api_user", on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT)


class Image(models.Model):
    name = models.CharField()


class ImageFile(models.Model):
    resolution = models.ForeignKey(ThumbnailResolution, on_delete=models.PROTECT)
    image = models.ForeignKey(Image, related_name="files", on_delete=models.CASCADE)
    image_file = models.ImageField()
