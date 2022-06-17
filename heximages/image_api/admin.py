from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from image_api.models import ImageAPIUser, Tier, Image, Thumbnail, ThumbnailHeight


@admin.display(description="Tier")
def tier_name(object):
    return f"{object.image_api_user.tier.name}"


class ImageAPIUserInline(admin.StackedInline):
    model = ImageAPIUser
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (ImageAPIUserInline,)
    list_display = ('username', 'email', tier_name, 'is_staff')

    fieldsets = (
        (
            "Account data", {
                'fields': ('username', 'email', 'password', 'last_login', 'date_joined')
            }
        ),
        (
            "Permissions", {
                'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')
            }
        ),
    )


admin.site.unregister(Group)  # Groups aren't used in this app

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(ThumbnailHeight)
admin.site.register(Tier)
admin.site.register(Image)
admin.site.register(Thumbnail)
