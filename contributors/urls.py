# contributors/urls.py

from django.urls import path
from .views import (
    TopContributorListAPIView,
    TopContributorCreateAPIView,
    TopContributorDetailAPIView,
)

urlpatterns = [
    path('', TopContributorListAPIView.as_view(), name='top-contributor-list'),
    path('create/', TopContributorCreateAPIView.as_view(), name='top-contributor-create'),
    path('<int:pk>/', TopContributorDetailAPIView.as_view(), name='top-contributor-detail'),
]
