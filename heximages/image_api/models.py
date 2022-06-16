from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.dispatch import receiver

from io import BytesIO
from pathlib import Path
from PIL import Image as PILImage

import os
import shutil


def original_image_path(instance, filename):
    """Helper function to generate the path that original images should be uploaded to"""
    return f"{instance.name}/original/{filename}"


def thumbnail_path(instance, filename):
    """Helper function to generate the path that thumbnails should be uploaded to"""
    return f"{instance.image.name}/{instance.thumbnail_height.height}/{filename}"


def resize_image_to_thumbnail(original_image, height):
    """Resize the original image and save it to a ContentFile"""
    original_image_pil = PILImage.open(original_image)
    if original_image_pil.size[1] > height:
        scale = height / original_image_pil.size[1]  # calculate the scale by which the height is being resized
        new_width = round(original_image_pil.size[0] * scale)  # resize the width by the same scale
        new_image_pil = original_image_pil.resize((new_width, height))
    if new_image_pil.mode in ("RGBA", "P"):
        new_image_pil = new_image_pil.convert("RGB")
    buffer = BytesIO()  # temporary buffer to save the image to
    new_image_pil.save(fp=buffer, format="JPEG")
    return ContentFile(buffer.getvalue())


def create_thumbnail(image, height):
    """Create a new Thumbnail object with the specified height"""
    thumbnail_pil = resize_image_to_thumbnail(image.file, height)
    new_thumbnail = Thumbnail.objects.create(thumbnail_height=ThumbnailHeight.objects.get(height=height), image=image)
    new_thumbnail.file.save(os.path.basename(image.file.name), InMemoryUploadedFile(
        thumbnail_pil,
        None,
        os.path.basename(image.file.name),
        'image/jpeg',
        thumbnail_pil.tell,
        None
    ))
    new_thumbnail.save()


class ThumbnailHeight(models.Model):
    """Model to store possible thumbnail heights"""
    height = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.height}px"


class Tier(models.Model):
    """Model to store account tiers"""
    name = models.CharField(max_length=50)
    thumbnail_heights = models.ManyToManyField(ThumbnailHeight)  # thumbnail heights available to users with this tier
    can_get_original = models.BooleanField(default=False)  # if True, users with this tier can get the link to the original image
    can_get_temporary = models.BooleanField(default=False)  # if True, users with this tier can generate a temporary link to their image

    def __str__(self):
        return f"{self.name}"


class ImageAPIUser(models.Model):
    """Model to store the tier of the account"""
    auth_user = models.OneToOneField(User, related_name="image_api_user", on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT)

    def __str__(self):
        return f"User {self.auth_user.username} on {self.tier.name} tier"

    def save(self, *args, **kwargs):
        """
        The save function is overridden to update all thumbnails when the user switches tiers.
        This could probably be heavily optimized, but switching tiers shouldn't occur often
        enough to cause issues.
        """
        super().save(*args, **kwargs)

        images = self.images
        for image in images.all():
            thumbnails = image.thumbnails.all()
            existing_heights = set(map(lambda x: x.thumbnail_height.height, thumbnails))
            correct_heights = set(map(lambda x: x.height, self.tier.thumbnail_heights.all()))
            added_heights = list(correct_heights - existing_heights)  # get all the thumbnail heights that the user gained access to
            removed_resolutions = list(existing_heights - correct_heights)  # get all the thumbnail heights that the user lost access to
            for thumbnail in thumbnails:
                if thumbnail.thumbnail_height.height in removed_resolutions:
                    thumbnail.delete()
            for height in added_heights:
                create_thumbnail(image, height)


class Image(models.Model):
    """Model to store the original image and all related thumbnails"""
    name = models.CharField(max_length=100)
    user = models.ForeignKey(ImageAPIUser, related_name="images", on_delete=models.CASCADE)
    file = models.ImageField(upload_to=original_image_path)

    def __str__(self):
        return f"Image {self.name} uploaded by {self.user.auth_user.username}"

    def save(self, *args, **kwargs):
        """
        The save function is overridden to make sure the thumbnail state is synchronized between the DB and the filesystem.
        The state should never be desynchronized, but just in case, it is checked.
        """
        super().save(*args, **kwargs)

        existing_thumbnail_heights = map(lambda x: x.thumbnail_height, self.thumbnails.all())

        correct_thumbnail_heights = self.user.tier.thumbnail_heights.all()
        if existing_thumbnail_heights != correct_thumbnail_heights:
            for thumbnail_height in correct_thumbnail_heights:
                if thumbnail_height not in existing_thumbnail_heights:
                    create_thumbnail(self, thumbnail_height.height)
            
            for thumbnail_height in existing_thumbnail_heights:
                if thumbnail_height not in correct_thumbnail_heights:
                    self.thumbnails.get(thumbnail_height=thumbnail_height).delete()


class Thumbnail(models.Model):
    """Model to store a thumbnail of an image"""
    thumbnail_height = models.ForeignKey(ThumbnailHeight, on_delete=models.PROTECT)
    image = models.ForeignKey(Image, related_name="thumbnails", on_delete=models.CASCADE)
    file = models.ImageField(upload_to=thumbnail_path)

    def __str__(self):
        return f"{self.thumbnail_height.__str__()} thumbnail of image {self.image.name}"


@receiver(models.signals.post_delete, sender=Thumbnail)
def delete_thumbnails_on_delete(sender, instance, **kwargs):
    """This function deletes a thumbnail file and it's corresponding folder when a thumbnail is deleted"""
    directory = Path(instance.file.path).parent
    if instance.file:
        if os.path.isdir(directory):
            shutil.rmtree(directory)


@receiver(models.signals.post_delete, sender=Image)
def delete_image_on_delete(sender, instance, **kwargs):
    """This function deletes every file related to an image that has been deleted"""
    directory = Path(instance.file.path).parents[1]
    if instance.file:
        if os.path.isdir(directory):
            shutil.rmtree(directory)
