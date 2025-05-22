from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import PodcastTag, Podcast
from .serializers import PodcastTagSerializer, PodcastSerializer
from common.views import CustomJWTAuthentication


class PodcastTagListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

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
            return [IsAuthenticated()]
        return [AllowAny()]



# JWT-protected CRUD views
class PodcastListCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
class PublicPublishedPodcastListAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        podcast_id = request.query_params.get("id")
        if podcast_id:
            podcast = generics.get_object_or_404(Podcast, pk=podcast_id, is_published=True)
            serializer = PodcastSerializer(podcast)
            return Response(serializer.data)

        podcasts = Podcast.objects.filter(is_published=True).order_by("-published_date")
        serializer = PodcastSerializer(podcasts, many=True)
        return Response(serializer.data)
