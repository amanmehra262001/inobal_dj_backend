# blog/urls.py

from django.urls import path
from .views import BlogListCreateAPIView, BlogDetailAPIView, BlogTagListCreateView, BlogTagDetailView, ListS3Images,S3ImageManager, PublishedBlogListAPIView, PublishedBlogDetailAPIView, UserBlogDetailAPIView, UserBlogListCreateAPIView

urlpatterns = [
    path('tags/', BlogTagListCreateView.as_view(), name='blogtag-list-create'),
    path('tags/<int:pk>/', BlogTagDetailView.as_view(), name='blogtag-delete'),
    path('', BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('details/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
    path('list-images/', ListS3Images.as_view(), name='list-images'),
    path('s3-image/', S3ImageManager.as_view(), name='blog-images-manager'),

    # user apis
    path('user/', UserBlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('user/details/<int:pk>/', UserBlogDetailAPIView.as_view(), name='blog-detail'),

    # public apis
    path('published/', PublishedBlogListAPIView.as_view(), name='published-blog-list'),
    path('published/<int:pk>/', PublishedBlogDetailAPIView.as_view(), name='published-blog-detail'),
]
