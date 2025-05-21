# contributors/urls.py

from django.urls import path
from .views import (
    TopContributorListAPIView,
    TopContributorCreateAPIView,
    TopContributorDetailAPIView,

    S3ContributorsImageManager
)

urlpatterns = [
    path('', TopContributorListAPIView.as_view(), name='top-contributor-list'),
    path('create/', TopContributorCreateAPIView.as_view(), name='top-contributor-create'),
    path('<int:pk>/', TopContributorDetailAPIView.as_view(), name='top-contributor-detail'),

    path('s3-image/', S3ContributorsImageManager.as_view(), name='magazine-s3-manager'),
]
