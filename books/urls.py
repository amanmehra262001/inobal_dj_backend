from django.urls import path
from .views import S3BooksImageManager, BookTagListCreateView, BookTagDetailDeleteView, PublicPublishedBookDetailAPIView, PublicPublishedBooksAPIView, BookListCreateAPIView, BookDetailAPIView

urlpatterns = [
    path("tags/", BookTagListCreateView.as_view(), name="book-tag-list-create"),
    path("tags/<int:pk>/", BookTagDetailDeleteView.as_view(), name="book-tag-delete"),

    path("", BookListCreateAPIView.as_view(), name="book-list-create"),
    path("details/<int:pk>/", BookDetailAPIView.as_view(), name="book-detail"),
    path("published/", PublicPublishedBooksAPIView.as_view(), name="published-books"),
    path("published/<int:pk>/", PublicPublishedBookDetailAPIView.as_view(), name="published-book-detail"),


    path('s3-image/', S3BooksImageManager.as_view(), name='podcast-s3-image-manager'),
]
