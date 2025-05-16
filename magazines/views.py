# magazines/views.py

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from magazines.models import Magazine, MagazineTag
from .serializers import MagazineSerializer, MagazineTagSerializer
from common.views import CustomJWTAuthentication
from datetime import datetime
from django.db.models.functions import ExtractYear

# --- TAG Views ---

class MagazineTagListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

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
    permission_classes = [IsAuthenticated]


# --- Magazine Views ---

class MagazineListCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

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
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

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




class PublicMagazinesByYearView(APIView):
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