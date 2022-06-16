from django.contrib import admin
from image_api.models import ImageAPIUser, Tier, Image, Thumbnail, ThumbnailHeight

# Register your models here.

admin.site.register(ThumbnailHeight)
admin.site.register(Tier)
admin.site.register(ImageAPIUser)
admin.site.register(Image)
admin.site.register(Thumbnail)
