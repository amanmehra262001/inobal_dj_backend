from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from .models import PodcastTag, Podcast
from .serializers import PodcastTagSerializer, PodcastSerializer, PodcastListSerializer
from common.views import CustomJWTAuthentication, IsAdminUser
from common.constants import S3_PODCASTS_BUCKET_NAME, S3_BLOG_BUCKET_NAME
from rest_framework.parsers import MultiPartParser, FormParser
from common.utils.s3_utils import upload_image_to_s3, delete_image_from_s3
from rest_framework.pagination import PageNumberPagination


class PodcastTagListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        tags = PodcastTag.objects.all()
        serializer = PodcastTagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PodcastTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # slug is auto-generated
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PodcastTagDetailView(generics.DestroyAPIView):
    queryset = PodcastTag.objects.all()
    serializer_class = PodcastTagSerializer
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdminUser()]
        return [AllowAny()]



# JWT-protected CRUD views
class PodcastListCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        podcasts = Podcast.objects.all()
        serializer = PodcastSerializer(podcasts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PodcastSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PodcastDetailAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return generics.get_object_or_404(Podcast, pk=pk)

    def get(self, request, pk):
        podcast = self.get_object(pk)
        serializer = PodcastSerializer(podcast)
        return Response(serializer.data)

    def put(self, request, pk):
        podcast = self.get_object(pk)
        serializer = PodcastSerializer(podcast, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        podcast = self.get_object(pk)
        podcast.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Public View for Published Podcasts
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PublicPublishedPodcastListAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        podcast_id = request.query_params.get("id")
        sort_order = request.query_params.get("sort", "newest")

        if podcast_id:
            podcast = generics.get_object_or_404(Podcast, pk=podcast_id, is_published=True)
            serializer = PodcastSerializer(podcast)
            return Response(serializer.data)

        # Determine ordering
        ordering = "-published_date" if sort_order == "newest" else "published_date"

        podcasts = Podcast.objects.filter(is_published=True).defer('transcript').order_by(ordering)

        paginator = StandardResultsSetPagination()
        paginated_qs = paginator.paginate_queryset(podcasts, request)
        serializer = PodcastListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicPublishedPodcastListAPIViewByTags(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        tags_param = request.query_params.get("tags", "")
        sort_order = request.query_params.get("sort", "newest")

        tag_names = [tag.strip() for tag in tags_param.split(",") if tag.strip()]
        tag_qs = PodcastTag.objects.filter(name__in=tag_names)

        ordering = "-published_date" if sort_order == "newest" else "published_date"

        books = (
            Podcast.objects.filter(is_published=True)
            .filter(tags__in=tag_qs)
            .distinct()
            .order_by(ordering)
        )

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(books, request)
        serializer = PodcastListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# S3 integration
class S3PodcastsFileManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Upload a file (image or PDF) to S3 under a folder.
        Send as form-data:
        - file (required)
        - folder (optional: defaults to 'podcasts')
        """
        upload_file = request.FILES.get('file')
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


class S3PodcastsImageManager(APIView):
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
