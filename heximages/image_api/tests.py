from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from image_api.models import ThumbnailHeight, Tier, ImageAPIUser, Image, Thumbnail
from django.conf import settings
import os
import shutil
from PIL import Image as PILImage
from rest_framework.test import APIClient


class CreateThumbnailsTestCase(TestCase):
    def setUp(self):
        th200 = ThumbnailHeight.objects.create(height=200)
        tier = Tier.objects.create(name="testtier")
        tier.thumbnail_heights.add(th200)
        tier.save()
        user = User.objects.create(username="testuser", password="testuserpw")
        iapiu = ImageAPIUser.objects.create(auth_user=user, tier=tier)
        image = Image(name="testimage", user=iapiu)
        image.file = SimpleUploadedFile(name='TestImage.png', content=open(settings.BASE_DIR / "image_api/test_files/TestImage.png", 'rb').read(), content_type='image/png')
        image.save()

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT / "testuser")

    def test_image_uploaded(self):
        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage/original"))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT / "testuser/testimage/original/TestImage.png"))

    def test_thumbnail_created(self):
        pil_file = PILImage.open(Thumbnail.objects.get(image__name="testimage").file)
        self.assertTrue(pil_file.size[1] == 200)
        self.assertTrue(pil_file.format == "JPEG")
        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage/200"))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT / "testuser/testimage/200/TestImage.jpg"))

    def test_tier_switch(self):
        th400 = ThumbnailHeight.objects.create(height=400)
        tier = Tier.objects.create(name="testtier2")
        tier.thumbnail_heights.add(th400)
        tier.save()
        iapiu = ImageAPIUser.objects.get(auth_user__username="testuser")
        iapiu.tier = tier
        iapiu.save()

        self.assertFalse(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage/200"))
        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage/400"))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT / "testuser/testimage/400/TestImage.jpg"))


class ImageAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        th200 = ThumbnailHeight.objects.create(height=200)
        tier = Tier.objects.create(name="testtier")
        tier.thumbnail_heights.add(th200)
        tier.save()
        user = User.objects.create(username="testuser", password="testuserpw")
        self.client.force_authenticate(user=user)
        iapiu = ImageAPIUser.objects.create(auth_user=user, tier=tier)
        image = Image(name="testimage", user=iapiu)
        image.file = SimpleUploadedFile(name='TestImage.png', content=open(settings.BASE_DIR / "image_api/test_files/TestImage.png", 'rb').read(), content_type='image/png')
        image.save()

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT / "testuser")

    def test_post(self):
        image_file = SimpleUploadedFile(name='TestImage.png', content=open(settings.BASE_DIR / "image_api/test_files/TestImage.png", 'rb').read(), content_type='image/png')
        self.client.post('/images/', {"name": "testimage2", "file": image_file})

        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage2/original"))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT / "testuser/testimage2/original/TestImage.png"))
        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT / "testuser/testimage/200"))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT / "testuser/testimage/200/TestImage.jpg"))
