# magazines/views.py

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from magazines.models import Magazine, MagazineTag, FeaturedPerson, MagazinePage
from .serializers import MagazineSerializer, MagazineTagSerializer, FeaturedPersonSerializer, FeaturedPersonDetailSerializer, FeaturedPersonListSerializer, MagazinePageSerializer
from common.views import CustomJWTAuthentication, IsAdminUser
from datetime import datetime
from common.constants import S3_MAGAZINE_BUCKET_NAME, S3_BLOG_BUCKET_NAME
from rest_framework.parsers import MultiPartParser, FormParser
from common.utils.s3_utils import upload_image_to_s3, delete_image_from_s3
from django.conf import settings
from django.shortcuts import get_object_or_404

from django.db.models.functions import ExtractYear
from django.db.models import Count


# --- TAG Views ---
class MagazineTagListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        tags = MagazineTag.objects.all()
        serializer = MagazineTagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MagazineTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MagazineTagDeleteView(generics.DestroyAPIView):
    queryset = MagazineTag.objects.all()
    serializer_class = MagazineTagSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]


# --- Magazine Views ---
class MagazinePageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MagazinePageSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        magazine_id = self.kwargs['magazine_id']
        return MagazinePage.objects.filter(magazine__id=magazine_id).order_by('page_number')

    def perform_create(self, serializer):
        magazine_id = self.kwargs['magazine_id']
        magazine = get_object_or_404(Magazine, id=magazine_id)
        serializer.save(magazine=magazine)

class MagazineListCreateAPIView(APIView):
    queryset = Magazine.objects.all().prefetch_related('pages', 'tags')
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        magazines = Magazine.objects.all().order_by('-published_date')
        serializer = MagazineSerializer(magazines, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MagazineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MagazineDetailAPIView(APIView):
    queryset = Magazine.objects.all().prefetch_related('pages', 'tags')
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return generics.get_object_or_404(Magazine, pk=pk)

    def get(self, request, pk):
        magazine = self.get_object(pk)
        serializer = MagazineSerializer(magazine)
        return Response(serializer.data)

    def put(self, request, pk):
        magazine = self.get_object(pk)
        serializer = MagazineSerializer(magazine, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        magazine = self.get_object(pk)
        magazine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicMagazineDetailView(APIView):
    queryset = Magazine.objects.all().prefetch_related('pages', 'tags')
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk):
        magazine = get_object_or_404(Magazine, id=pk, is_published=True)
        serializer = MagazineSerializer(magazine)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicMagazinesByYearView(APIView):
    queryset = Magazine.objects.all().prefetch_related('pages', 'tags')
    permission_classes = [AllowAny]  # ✅ public
    authentication_classes = []

    def get(self, request, year):
        try:
            year = int(year)
        except ValueError:
            return Response({"detail": "Invalid year format."}, status=400)

        magazines = Magazine.objects.filter(
            is_published=True,
            published_date__year=year
        ).order_by('-published_date')

        serializer = MagazineSerializer(magazines, many=True)
        return Response(serializer.data, status=200)
    

class PublicMagazinesForCurrentView(APIView):
    permission_classes = [AllowAny]  # ✅ public
    authentication_classes = []

    def get(self, request):
        magazine = Magazine.objects.filter(is_published=True).order_by('published_date').first()

        magazine = {
            'id': magazine.id,
            'name': magazine.name,
            'published_date': magazine.published_date,
            'cover_image_url': magazine.cover_image_url if magazine.cover_image_url else None,
            'cover_image_key': magazine.cover_image_key if magazine.cover_image_key else None,
            'description': magazine.description,
            'is_published': magazine.is_published,
            'show_on_home': magazine.show_on_home,
            'on_home_priority': magazine.on_home_priority
        }

        # serializer = MagazineSerializer(magazines, many=True)
        return Response(magazine, status=200)
    

class PublicMagazinesForHomeView(APIView):
    permission_classes = [AllowAny]  # ✅ public
    authentication_classes = []

    def get(self, request):
        magazines = Magazine.objects.filter(show_on_home=True).order_by('on_home_priority')

        serializer = MagazineSerializer(magazines, many=True)
        return Response(serializer.data, status=200)
    

class MagazineYearsAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        years = (
            Magazine.objects.filter(is_published=True)
            .annotate(year=ExtractYear('published_date'))
            .values('year')
            .annotate(count=Count('id'))
            .order_by('-year')
            .values_list('year', flat=True)
        )
        return Response(list(years), status=status.HTTP_200_OK)



# Featured People API
# View to get all featured people for a magazine (list, no long_description)
class FeaturedPeopleByMagazineView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, magazine_id):
        people = FeaturedPerson.objects.filter(magazine_id=magazine_id)
        serializer = FeaturedPersonListSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# View to get a single featured person with full details
class FeaturedPersonDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        person = get_object_or_404(FeaturedPerson, pk=pk)

        # Get the queryset ordered by id (or any other logic like created_at)
        all_people = FeaturedPerson.objects.filter(magazine=person.magazine).order_by('id')
        ids = list(all_people.values_list('id', flat=True))
        
        current_index = ids.index(person.id)
        previous_id = ids[current_index - 1] if current_index > 0 else None
        next_id = ids[current_index + 1] if current_index < len(ids) - 1 else None

        serializer = FeaturedPersonDetailSerializer(person)
        data = serializer.data
        data['previous_id'] = previous_id
        data['next_id'] = next_id

        return Response(data, status=status.HTTP_200_OK)

class CreateFeaturedPersonView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request, magazine_id):
        magazine = get_object_or_404(Magazine, id=magazine_id)
        data = request.data.copy()
        data['magazine'] = magazine.id
        serializer = FeaturedPersonSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateFeaturedPersonView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        person = get_object_or_404(FeaturedPerson, id=pk)
        serializer = FeaturedPersonSerializer(person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteFeaturedPersonView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        person = get_object_or_404(FeaturedPerson, id=pk)
        person.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# S3 integration
class S3MagazineFileManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Upload multiple ordered images to a specific magazine folder.
        Send as form-data:
        - files[] (required): multiple images
        - magazine_id (required): ID used as folder name
        """
        files = request.FILES.getlist('files')
        magazine_id = request.data.get('magazine_id')

        if not magazine_id:
            return Response({'error': 'magazine_id is required'}, status=400)
        if not files:
            return Response({'error': 'No files provided'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        folder = f'magazines/{magazine_id}'

        uploaded = []

        for index, image_file in enumerate(files):
            # Ensure ordering: page_001.jpg, page_002.jpg...
            page_number = index + 1
            file_ext = image_file.name.split('.')[-1].lower()
            image_file.name = f'page_{page_number:03d}.{file_ext}'

            response = upload_image_to_s3(image_file=image_file, folder=folder, bucket=bucket)

            if response['error']:
                return Response({'error': f"Failed to upload page {page_number}", 'message': response['message']}, status=400)

            uploaded.append({
                'url': response['url'],
                'key': response['key'],
                'page': page_number
            })

        return Response({
            'message': f"{len(uploaded)} pages uploaded",
            'pages': uploaded
        }, status=200)
    
    
    def delete(self, request):
        """
        Delete a specific page from a magazine by its key:
        /api/s3-magazine/?key=magazines/123/page_003.jpg
        """
        file_key = request.query_params.get('key')

        if not file_key:
            return Response({'error': 'File key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = delete_image_from_s3(bucket=bucket, image_key=file_key)

        if not response['error']:
            return Response({'message': 'Page deleted successfully'}, status=200)

        return Response({'error': response['message']}, status=400)


    def put(self, request):
        """
        Replace a specific page in a magazine.
        Send as form-data:
        - file: new image
        - magazine_id: ID
        - page: page number to replace (starts at 1)
        """
        image_file = request.FILES.get('file')
        magazine_id = request.data.get('magazine_id')
        page = request.data.get('page')

        if not (image_file and magazine_id and page):
            return Response({'error': 'file, magazine_id and page are required'}, status=400)

        try:
            page = int(page)
        except ValueError:
            return Response({'error': 'Page must be an integer'}, status=400)

        try:
            magazine = Magazine.objects.get(id=magazine_id)
        except Magazine.DoesNotExist:
            return Response({'error': 'Magazine not found'}, status=404)

        # Compose key
        bucket = S3_BLOG_BUCKET_NAME
        folder = f'magazines/{magazine_id}'
        file_ext = image_file.name.split('.')[-1].lower()
        image_file.name = f'page_{page:03d}.{file_ext}'
        key = f'{folder}/{image_file.name}'

        # Delete from S3 first
        delete_image_from_s3(bucket=bucket, image_key=key)

        # Upload to S3
        response = upload_image_to_s3(image_file=image_file, folder=folder, bucket=bucket)

        if response['error']:
            return Response({'error': 'Failed to replace page', 'message': response['message']}, status=400)

        # ✅ UPDATE EXISTING RECORD OR CREATE NEW ONE
        MagazinePage.objects.update_or_create(
            magazine=magazine,
            page_number=page,
            defaults={
                'image_url': response['url'],
                'image_key': response['key'],
            }
        )

        return Response({
            'message': 'Page replaced',
            'url': response['url'],
            'key': response['key']
        }, status=200)



# class S3MagazineFileManager(APIView):
#     parser_classes = (MultiPartParser, FormParser)
#     authentication_classes = [CustomJWTAuthentication]
#     permission_classes = [IsAdminUser]

#     def post(self, request):
#         """
#         Upload a file (image or PDF) to S3 under a folder.
#         Send as form-data:
#         - file (required)
#         - folder (optional: defaults to 'magazines')
#         """
#         upload_file = request.FILES.get('file')
#         folder = request.data.get('folder', 'misc')

#         if not upload_file:
#             return Response({'error': 'No file provided'}, status=400)

#         bucket = S3_BLOG_BUCKET_NAME
#         response = upload_image_to_s3(image_file=upload_file, folder=folder, bucket=bucket)

#         if not response['error']:
#             return Response({
#                 'message': response['message'],
#                 'url': response['url'],
#                 'key': response['key']
#             }, status=200)
        
#         return Response({'message': response['message']}, status=400)

#     def delete(self, request):
#         """
#         Delete a file from S3 by its key:
#         /api/s3-magazine/?key=magazines/filename.pdf
#         """
#         file_key = request.query_params.get('key')

#         if not file_key:
#             return Response({'error': 'File key is required'}, status=400)

#         bucket = S3_BLOG_BUCKET_NAME
#         response = delete_image_from_s3(bucket=bucket, image_key=file_key)

#         if not response['error']:
#             return Response({'message': response['message']}, status=200)

#         return Response({'message': response['message']}, status=400)


class S3MagazineImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Upload a file (image or PDF) to S3 under a folder.
        Send as form-data:
        - file (required)
        - folder (optional: defaults to 'magazines')
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
        /api/s3-magazine/?key=magazines/filename.pdf
        """
        file_key = request.query_params.get('key')

        if not file_key:
            return Response({'error': 'File key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = delete_image_from_s3(bucket=bucket, image_key=file_key)

        if not response['error']:
            return Response({'message': response['message']}, status=200)

        return Response({'message': response['message']}, status=400)

        
class S3MagazineFeaturedImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Upload a file (image or PDF) to S3 under a folder.
        Send as form-data:
        - file (required)
        - folder (optional: defaults to 'magazines')
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
        /api/s3-magazine/?key=magazines/filename.pdf
        """
        file_key = request.query_params.get('key')

        if not file_key:
            return Response({'error': 'File key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = delete_image_from_s3(bucket=bucket, image_key=file_key)

        if not response['error']:
            return Response({'message': response['message']}, status=200)

        return Response({'message': response['message']}, status=400)
