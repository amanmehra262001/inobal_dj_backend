from django.urls import path
from .views import S3BooksImageManager, BookTagListCreateView, BookTagDetailDeleteView, PublicPublishedBookDetailAPIView, PublicPublishedBooksAPIView, BookListCreateAPIView, BookDetailAPIView, S3BooksHomeImageManager, PublishedS3BooksHomeImageManager, PublicPublishedBooksAPIViewByTags, HomePublicBookView, HomeAdminBookView, HomePublicBookImageView

urlpatterns = [
    path("tags/", BookTagListCreateView.as_view(), name="book-tag-list-create"),
    path("tags/<int:pk>/", BookTagDetailDeleteView.as_view(), name="book-tag-delete"),

    path("", BookListCreateAPIView.as_view(), name="book-list-create"),
    path("details/<int:pk>/", BookDetailAPIView.as_view(), name="book-detail"),
    path("published/", PublicPublishedBooksAPIView.as_view(), name="published-books"),
    path("published/<int:pk>/", PublicPublishedBookDetailAPIView.as_view(), name="published-book-detail"),
    path("published/by-tags/", PublicPublishedBooksAPIViewByTags.as_view(), name="published-books-by-tags"),

    path('home/details/', HomePublicBookView.as_view(), name='books-home-details'),
    path('home/images/', HomePublicBookImageView.as_view(), name='books-home-images'),
    
    path('home/admin/', HomeAdminBookView.as_view(), name='books-home-details-admin-manager'),

    path('s3-image/', S3BooksImageManager.as_view(), name='books-s3-image-manager'),
    path('s3-image/home/', S3BooksHomeImageManager.as_view(), name='books-home-s3-image-manager'),
    path('s3-image/home/published/', PublishedS3BooksHomeImageManager.as_view(), name='published-books-home-s3-image-manager'),
]
