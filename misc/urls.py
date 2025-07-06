# careers/urls.py

from django.urls import path
from .views import CareerListCreateAPIView, CareerDetailAPIView, PublishedCareerListCreateAPIView, BlogNotificationListAPIView, AdvertisementPublicView, AdvertisementAdminView, S3ImageManager

urlpatterns = [
    path('careers/', CareerListCreateAPIView.as_view(), name='career-list-create'),
    path('careers/published/', PublishedCareerListCreateAPIView.as_view(), name='published-career-list-create'),
    path('careers/<int:pk>/', CareerDetailAPIView.as_view(), name='career-detail'),
    path('notifications/', BlogNotificationListAPIView.as_view(), name='career-detail'),

    path('ads/', AdvertisementPublicView.as_view(), name='ads-public'),
    path('ads/admin/', AdvertisementAdminView.as_view(), name='ads-admin-create'),
    path('ads/admin/<int:pk>/', AdvertisementAdminView.as_view(), name='ads-admin-update'),
    path('ads/images/', S3ImageManager.as_view(), name='ads-image-manager'),
]
