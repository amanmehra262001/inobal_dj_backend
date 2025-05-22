# contributors/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import TopContributor
from .serializers import TopContributorSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from common.views import CustomJWTAuthentication  # Your custom JWT class if any

from common.constants import S3_CONTRIBUTORS_BUCKET_NAME, S3_BLOG_BUCKET_NAME
from common.utils.s3_utils import upload_image_to_s3, delete_image_from_s3

# Public GET view with optional ?length=<number>
class TopContributorListAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        length = request.query_params.get('length')
        contributors = TopContributor.objects.all()

        if length and length.isdigit():
            contributors = contributors[:int(length)]

        serializer = TopContributorSerializer(contributors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# POST view
class TopContributorCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TopContributorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Detail view for GET, PUT, DELETE by ID
class TopContributorDetailAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        return generics.get_object_or_404(TopContributor, pk=pk)

    def get(self, request, pk):
        contributor = self.get_object(pk)
        serializer = TopContributorSerializer(contributor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        contributor = self.get_object(pk)
        serializer = TopContributorSerializer(contributor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        contributor = self.get_object(pk)
        contributor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class S3ContributorsImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Upload a file (image or PDF) to S3 under a folder.
        Send as form-data:
        - file (required)
        - folder (optional: defaults to 'contributors')
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