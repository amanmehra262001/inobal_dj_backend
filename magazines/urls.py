# magazines/urls.py

from django.urls import path
from .views import (
    MagazineTagListCreateView, MagazineTagDeleteView,
    MagazineListCreateAPIView, MagazineDetailAPIView, PublicMagazinesByYearView, PublicMagazinesForHomeView, PublicMagazinesForCurrentView, S3MagazineFileManager, S3MagazineImageManager, S3MagazineFeaturedImageManager, FeaturedPeopleByMagazineView, CreateFeaturedPersonView, UpdateFeaturedPersonView, DeleteFeaturedPersonView, FeaturedPersonDetailView, PublicMagazineDetailView, MagazineYearsAPIView
)

urlpatterns = [
    path('tags/', MagazineTagListCreateView.as_view(), name='magazine-tag-list-create'),
    path('tags/<int:pk>/', MagazineTagDeleteView.as_view(), name='magazine-tag-delete'),

    path('', MagazineListCreateAPIView.as_view(), name='magazine-list-create'),
    path('details/<int:pk>/', MagazineDetailAPIView.as_view(), name='magazine-detail'),
    path('details/public/<int:pk>/', PublicMagazineDetailView.as_view(), name='magazine-detail-public'),

    path('home/', PublicMagazinesForHomeView.as_view(), name='magazines-for-home'),
    path('home/current/', PublicMagazinesForCurrentView.as_view(), name='magazines-current'),
    path('year/<int:year>/', PublicMagazinesByYearView.as_view(), name='magazine-by-year'),
    path('years/', MagazineYearsAPIView.as_view(), name='magazine-years'),


    path('<int:magazine_id>/featured/', FeaturedPeopleByMagazineView.as_view(), name='featured-people-by-magazine'),
    path('featured/<int:pk>/', FeaturedPersonDetailView.as_view(), name='featured-person-detail'),
    path('<int:magazine_id>/featured/create/', CreateFeaturedPersonView.as_view(), name='create-featured-person'),
    path('featured/<int:pk>/update/', UpdateFeaturedPersonView.as_view(), name='update-featured-person'),
    path('featured/<int:pk>/delete/', DeleteFeaturedPersonView.as_view(), name='delete-featured-person'),


    path('s3/pages/', S3MagazineFileManager.as_view(), name='magazine-s3-manager'),
    path('s3-image/', S3MagazineImageManager.as_view(), name='magazine-s3-manager'),
    path('s3-featured-image/', S3MagazineFeaturedImageManager.as_view(), name='magazine-s3-manager'),
]
