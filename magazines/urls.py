# magazines/urls.py

from django.urls import path
from .views import (
    MagazineTagListCreateView, MagazineTagDeleteView,
    MagazineListCreateAPIView, MagazineDetailAPIView, PublicMagazinesByYearView, S3MagazineFileManager, S3MagazineImageManager
)

urlpatterns = [
    path('tags/', MagazineTagListCreateView.as_view(), name='magazine-tag-list-create'),
    path('tags/<int:pk>/', MagazineTagDeleteView.as_view(), name='magazine-tag-delete'),

    path('', MagazineListCreateAPIView.as_view(), name='magazine-list-create'),
    path('details/<int:pk>/', MagazineDetailAPIView.as_view(), name='magazine-detail'),

    path('year/<int:year>/', PublicMagazinesByYearView.as_view(), name='magazine-by-year'),

    path('s3/', S3MagazineFileManager.as_view(), name='magazine-s3-manager'),
    path('s3-image/', S3MagazineImageManager.as_view(), name='magazine-s3-manager'),
]
