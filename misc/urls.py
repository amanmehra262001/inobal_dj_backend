# careers/urls.py

from django.urls import path
from .views import CareerListCreateAPIView, CareerDetailAPIView, PublishedCareerListCreateAPIView, BlogNotificationListAPIView

urlpatterns = [
    path('careers/', CareerListCreateAPIView.as_view(), name='career-list-create'),
    path('careers/published/', PublishedCareerListCreateAPIView.as_view(), name='published-career-list-create'),
    path('careers/<int:pk>/', CareerDetailAPIView.as_view(), name='career-detail'),
    path('notifications/', BlogNotificationListAPIView.as_view(), name='career-detail'),
]
