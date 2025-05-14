# blog/urls.py

from django.urls import path
from .views import BlogListCreateAPIView, BlogDetailAPIView, BlogTagListCreateView

urlpatterns = [
    path('tags/', BlogTagListCreateView.as_view(), name='blogtag-list-create'),
    path('blogs/', BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('blogs/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
    path('blogs/images/', BlogDetailAPIView.as_view(), name='blog-detail'),
    path('blogs/images/<int:pk>', BlogDetailAPIView.as_view(), name='blog-detail'),
]
