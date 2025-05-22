from django.urls import path
from .views import PodcastTagListCreateView, PodcastTagDetailView, PodcastListCreateAPIView, PodcastDetailAPIView, PublicPublishedPodcastListAPIView, S3PodcastsFileManager, S3PodcastsImageManager

urlpatterns = [
    path('tags/', PodcastTagListCreateView.as_view(), name='podcast-tag-list-create'),
    path('tags/<int:pk>/', PodcastTagDetailView.as_view(), name='podcast-tag-delete'),

    path('podcasts/', PodcastListCreateAPIView.as_view(), name='podcast-list-create'),
    path('podcasts/<int:pk>/', PodcastDetailAPIView.as_view(), name='podcast-detail'),
    path('podcasts/public/', PublicPublishedPodcastListAPIView.as_view(), name='podcast-public'),

    path('s3/', S3PodcastsFileManager.as_view(), name='podcast-s3-manager'),
    path('s3-image/', S3PodcastsImageManager.as_view(), name='podcast-s3-image-manager'),
]
