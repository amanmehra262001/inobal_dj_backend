# contributors/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import TopContributor
from .serializers import TopContributorSerializer
from common.views import CustomJWTAuthentication  # Your custom JWT class if any

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
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return generics.get_object_or_404(TopContributor, pk=pk)

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
