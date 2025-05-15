# blog/urls.py

from django.urls import path
from .views import BlogListCreateAPIView, BlogDetailAPIView, BlogTagListCreateView, BlogsImagesAPIView, BlogTagDetailView

urlpatterns = [
    path('tags/', BlogTagListCreateView.as_view(), name='blogtag-list-create'),
    path('tags/<int:pk>/', BlogTagDetailView.as_view(), name='blogtag-delete'),
    path('', BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('blogs/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
    path('blogs/images/', BlogsImagesAPIView.as_view(), name='blog-detail'),
    path('blogs/images/<int:pk>', BlogsImagesAPIView.as_view(), name='blog-detail'),
]
