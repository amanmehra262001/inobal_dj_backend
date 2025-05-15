# blog/urls.py

from django.urls import path
from .views import BlogListCreateAPIView, BlogDetailAPIView, BlogTagListCreateView, BlogTagDetailView, ListS3Images,S3ImageManager

urlpatterns = [
    path('tags/', BlogTagListCreateView.as_view(), name='blogtag-list-create'),
    path('tags/<int:pk>/', BlogTagDetailView.as_view(), name='blogtag-delete'),
    path('', BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('details/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
    # path('blogs/images/', BlogsImagesAPIView.as_view(), name='blog-detail'),
    # path('blogs/images/<int:pk>', BlogsImagesAPIView.as_view(), name='blog-detail'),

    # path('image/', get_image_url),
    path('list-images/', ListS3Images.as_view(), name='list-images'),
    path('s3-image/', S3ImageManager.as_view(), name='blog-images-manager'),



]
