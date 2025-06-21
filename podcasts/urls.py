from django.urls import path
from .views import PodcastTagListCreateView, PodcastTagDetailView, PodcastListCreateAPIView, PodcastDetailAPIView, PublicPublishedPodcastListAPIView, S3PodcastsFileManager, S3PodcastsImageManager, PublicPublishedPodcastListAPIViewByTags

urlpatterns = [
    path('tags/', PodcastTagListCreateView.as_view(), name='podcast-tag-list-create'),
    path('tags/<int:pk>/', PodcastTagDetailView.as_view(), name='podcast-tag-delete'),

    path('', PodcastListCreateAPIView.as_view(), name='podcast-list-create'),
    path('details/<int:pk>/', PodcastDetailAPIView.as_view(), name='podcast-detail'),
    path('public/', PublicPublishedPodcastListAPIView.as_view(), name='podcast-public'),
    path('public/by-tags/', PublicPublishedPodcastListAPIViewByTags.as_view(), name='podcast-public-list-by-tags'),

    path('s3/', S3PodcastsFileManager.as_view(), name='podcast-s3-manager'),
    path('s3-image/', S3PodcastsImageManager.as_view(), name='podcast-s3-image-manager'),
]
