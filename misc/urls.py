# careers/urls.py

from django.urls import path
from .views import CareerListCreateAPIView, CareerDetailAPIView, PublishedCareerListCreateAPIView, BlogNotificationListAPIView, AdvertisementPublicView, AdvertisementAdminView, S3ImageManager, EventDetailView, EventDetailAdminView, ActivityAdminView, EventFormCreateView, EventFormListAdminView, S3DocumentManager, EventCreateAdminView

urlpatterns = [
    path('careers/', CareerListCreateAPIView.as_view(), name='career-list-create'),
    path('careers/published/', PublishedCareerListCreateAPIView.as_view(), name='published-career-list-create'),
    path('careers/<int:pk>/', CareerDetailAPIView.as_view(), name='career-detail'),
    path('notifications/', BlogNotificationListAPIView.as_view(), name='career-detail'),

    path('ads/', AdvertisementPublicView.as_view(), name='ads-public'),
    path('ads/admin/', AdvertisementAdminView.as_view(), name='ads-admin-create'),
    path('ads/admin/<int:pk>/', AdvertisementAdminView.as_view(), name='ads-admin-update'),
    path('ads/images/', S3ImageManager.as_view(), name='ads-image-manager'),

    # Activities (nested under Event)
    path('events/<int:event_id>/activities/', ActivityAdminView.as_view(), name='activity-admin'),

    # EventForm submission (public)
    path('eventforms/submit/', EventFormCreateView.as_view(), name='eventform-submit'),
    path('eventforms/document/', S3DocumentManager.as_view(), name='eventform-document-manager'),
    path('events/manage/admin/images/', S3ImageManager.as_view(), name='events-image-manager'),

    # Event admin endpoints
    path('events/', EventDetailView.as_view(), name='event-details'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event-details-slug'),
    path('events/admin/create/', EventCreateAdminView.as_view(), name='event-admin-create'),
    path('events/admin/<slug:slug>/', EventDetailAdminView.as_view(), name='event-admin-detail'),

    # EventForm view (admin only)
    path('eventforms/all/', EventFormListAdminView.as_view(), name='eventform-list'),
]
