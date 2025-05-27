from django.urls import path
from .views import S3BooksImageManager, BookTagListCreateView, BookTagDetailDeleteView, PublicPublishedBookDetailAPIView, PublicPublishedBooksAPIView

urlpatterns = [
    path("book-tags/", BookTagListCreateView.as_view(), name="book-tag-list-create"),
    path("book-tags/<int:pk>/", BookTagDetailDeleteView.as_view(), name="book-tag-delete"),

    path("books/published/", PublicPublishedBooksAPIView.as_view(), name="published-books"),
    path("books/published/<int:pk>/", PublicPublishedBookDetailAPIView.as_view(), name="published-book-detail"),


    path('s3-image/', S3BooksImageManager.as_view(), name='podcast-s3-image-manager'),
]
