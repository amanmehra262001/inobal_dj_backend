from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from .models import Book, BookTag, BooksHomeImages
from .serializers import BookSerializer, BookTagSerializer, BooksHomeImagesSerializer
from common.views import CustomJWTAuthentication, IsAdminUser
from common.constants import S3_BOOKS_BUCKET_NAME, S3_BLOG_BUCKET_NAME
from rest_framework.parsers import MultiPartParser, FormParser
from common.utils.s3_utils import upload_image_to_s3, delete_image_from_s3
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import json

# Create your views here.

class BookTagListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        tags = BookTag.objects.all().order_by("name")
        serializer = BookTagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # slug is auto-generated in model
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookTagDetailDeleteView(generics.DestroyAPIView):
    queryset = BookTag.objects.all()
    serializer_class = BookTagSerializer
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        return [IsAdminUser()]



# JWT-protected: GET (detail), POST, PUT, DELETE
class BookListCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        books = Book.objects.all().order_by('-published_date')
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return generics.get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        book = self.get_object(pk)
        serializer = BookSerializer(book)
        return Response(serializer.data)

    def put(self, request, pk):
        book = self.get_object(pk)
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self.get_object(pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# Public & paginated: GET only for published books
class PublicPublishedBooksAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        books = Book.objects.filter(is_published=True).order_by('-published_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(books, request)
        serializer = BookSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicPublishedBooksAPIViewByTags(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        # Step 1: Get the 'tags' query parameter (comma-separated)
        tags_param = request.query_params.get("tags", "")
        tag_names = [tag.strip() for tag in tags_param.split(",") if tag.strip()]

        # Step 2: Get tag objects that match the names
        tag_qs = BookTag.objects.filter(name__in=tag_names)

        # Step 3: Filter books with those tags, and published
        books = (
            Book.objects.filter(is_published=True)
            .filter(tags__in=tag_qs)
            .distinct()
            .order_by('-published_date')
        )

        # Step 4: Paginate and return the result
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(books, request)
        serializer = BookSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicPublishedBookDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk, is_published=True)
        serializer = BookSerializer(book)
        return Response(serializer.data, status=200)



# S3
class S3BooksImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Upload a file (image or PDF) to S3 under a folder.
        Send as form-data:
        - file (required)
        - folder (optional: defaults to 'podcastss')
        """
        upload_file = request.FILES.get('image')
        folder = request.data.get('folder', 'misc')

        if not upload_file:
            return Response({'error': 'No file provided'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = upload_image_to_s3(image_file=upload_file, folder=folder, bucket=bucket)

        if not response['error']:
            return Response({
                'message': response['message'],
                'url': response['url'],
                'key': response['key']
            }, status=200)
        
        return Response({'message': response['message']}, status=400)

    def delete(self, request):
        """
        Delete a file from S3 by its key:
        /api/s3-podcasts/?key=podcastss/filename.pdf
        """
        file_key = request.query_params.get('key')

        if not file_key:
            return Response({'error': 'File key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = delete_image_from_s3(bucket=bucket, image_key=file_key)

        if not response['error']:
            return Response({'message': response['message']}, status=200)

        return Response({'message': response['message']}, status=400)


class S3BooksHomeImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        List all images in the BooksHomeImages model.
        """
        images = BooksHomeImages.objects.all().order_by('-created_at')
        serializer = BooksHomeImagesSerializer(images, many=True)
        return Response(serializer.data, status=200)


    def post(self, request):
        """
        Upload multiple files (images or PDFs) to S3 under a folder.
        Send as form-data:
        - image (can be one or multiple files)
        - folder (optional: defaults to 'misc')
        - priority (optional, can be sent per file or defaulted)
        """
        files = request.FILES.getlist('image')  # <-- handles multiple files
        folder = request.data.get('folder', 'misc')
        priority = int(request.data.get('priority', 0))

        if not files:
            return Response({'error': 'No files provided'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        uploaded = []

        for index, file in enumerate(files):
            response = upload_image_to_s3(image_file=file, folder=folder, bucket=bucket)
            if not response['error']:
                image_obj = BooksHomeImages.objects.create(
                    image_url=response['url'],
                    image_key=response['key'],
                    priority=priority + index  # Assign incremental priority
                )
                uploaded.append({
                    'message': response['message'],
                    'url': response['url'],
                    'key': response['key'],
                    'priority': image_obj.priority,
                })

        if uploaded:
            return Response({'uploaded': uploaded}, status=200)
        else:
            return Response({'message': 'No files uploaded successfully'}, status=400)


    def patch(self, request):
        """
        Update the priority of a specific image.
        Requires 'image_key' and a new 'priority' in the request body.
        """
        data = json.loads(request.body)
        image_key = data.get('image_key')
        new_priority = data.get('priority')
        print("image key:", image_key)
        print("new priority:", new_priority)

        if new_priority is None:
            return Response({'error': 'New priority is required.'}, status=400)

        try:
            new_priority = int(new_priority)
        except ValueError:
            return Response({'error': 'Priority must be an integer.'}, status=400)

        try:
            if image_key:
                image = BooksHomeImages.objects.get(image_key=image_key)
            else:
                return Response({'error': 'Either id or image_key must be provided.'}, status=400)
        except BooksHomeImages.DoesNotExist:
            return Response({'error': 'Image not found.'}, status=404)

        image.priority = new_priority
        image.save()

        return Response({
            'message': 'Priority updated successfully.',
            'id': image.id,
            'image_key': image.image_key,
            'new_priority': image.priority
        }, status=200)


    def delete(self, request):
        """
        Delete a file from S3 by its key:
        /api/s3-podcasts/?key=podcastss/filename.pdf
        """
        file_key = request.query_params.get('key')

        if not file_key:
            return Response({'error': 'File key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = delete_image_from_s3(bucket=bucket, image_key=file_key)

        if not response['error']:
            BooksHomeImages.objects.filter(image_key=file_key).delete()
            return Response({'message': response['message']}, status=200)

        return Response({'message': response['message']}, status=400)

        
        
        
class PublishedS3BooksHomeImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """
        List all images in the BooksHomeImages model.
        """
        images = BooksHomeImages.objects.all().order_by('priority')
        serializer = BooksHomeImagesSerializer(images, many=True)
        return Response(serializer.data, status=200)