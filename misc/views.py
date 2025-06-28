from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Career
from .serializers import CareerSerializer, BlogNotification, BlogNotificationSerializer
from django.shortcuts import get_object_or_404
from common.views import CustomJWTAuthentication, IsAdminUser
from rest_framework.permissions import AllowAny, IsAuthenticated

class CareerListCreateAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        careers = Career.objects.all()
        serializer = CareerSerializer(careers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CareerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CareerDetailAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return get_object_or_404(Career, pk=pk)

    def get(self, request, pk):
        career = self.get_object(pk)
        serializer = CareerSerializer(career)
        return Response(serializer.data)

    def put(self, request, pk):
        career = self.get_object(pk)
        serializer = CareerSerializer(career, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        career = self.get_object(pk)
        serializer = CareerSerializer(career, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        career = self.get_object(pk)
        career.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublishedCareerListCreateAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        careers = Career.objects.filter(is_published=True).order_by('priority')
        serializer = CareerSerializer(careers, many=True)
        return Response(serializer.data)
    

class BlogNotificationListAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = BlogNotification.objects.filter(user=user).order_by('-created_at')
        serializer = BlogNotificationSerializer(notifications, many=True)
        return Response(serializer.data)
