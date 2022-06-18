from django.urls import path, include
from rest_framework.routers import DefaultRouter
from image_api import views

router = DefaultRouter()
router.register(r'images', views.ImageViewSet, 'image')

urlpatterns = [
    path('', include(router.urls)),
]
