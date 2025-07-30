from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Career, Advertisement, Event, Activity, EventForm, Partners
from .serializers import CareerSerializer, BlogNotification, BlogNotificationSerializer, AdvertisementSerializer, EventFormSerializer, ActivitySerializer, EventSerializer, PartnersSerializer
from django.shortcuts import get_object_or_404
from common.views import CustomJWTAuthentication, IsAdminUser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from common.constants import S3_BLOG_BUCKET_NAME
from common.utils.s3_utils import delete_image_from_s3, upload_image_to_s3
import json

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


# Public GET View
class AdvertisementPublicView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        orientation = request.query_params.get("orientation")

        if orientation:
            try:
                ad = Advertisement.objects.get(orientation=orientation)
                serializer = AdvertisementSerializer(ad)
                return Response(serializer.data, status=200)
            except Advertisement.DoesNotExist:
                return Response({"error": "Advertisement not found"}, status=404)

        # If no orientation is specified, return both
        ads = Advertisement.objects.all()
        serializer = AdvertisementSerializer(ads, many=True)
        return Response(serializer.data, status=200)

# Admin-only POST and PATCH
class AdvertisementAdminView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdvertisementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            ad = Advertisement.objects.get(pk=pk)
        except Advertisement.DoesNotExist:
            return Response({"error": "Advertisement not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdvertisementSerializer(ad, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            ad = Advertisement.objects.get(pk=pk)
        except Advertisement.DoesNotExist:
            return Response({"error": "Advertisement not found"}, status=status.HTTP_404_NOT_FOUND)

        ad.delete()
        return Response({"message": "Advertisement deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# -------- Event Views --------
# Public View: List and Create Events
class EventDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug=None):
        if slug:
            try:
                event = Event.objects.get(slug=slug)
                serializer = EventSerializer(event)
                return Response(serializer.data)
            except Event.DoesNotExist:
                return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            events = Event.objects.all()
            serializer = EventSerializer(events, many=True)
            return Response(serializer.data)

            
# Create separate class for creating new events
class EventCreateAdminView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data.copy()
        activities_raw = request.POST.get("activities")
        if activities_raw:
            data['activities'] = json.loads(activities_raw)
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# Existing view for PATCH/DELETE based on slug
class EventDetailAdminView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_object(self, slug):
        try:
            return Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            return None

    def patch(self, request, slug):
        event = self.get_object(slug)
        if not event:
            return Response({"error": "Not found"}, status=404)

        # Convert QueryDict to a normal dict first
        data = dict(request.data)

        # Flatten single-value fields
        for k, v in data.items():
            if isinstance(v, list) and len(v) == 1:
                data[k] = v[0]

        # Handle activities
        activities_raw = data.get("activities") or request.POST.get("activities")
        if activities_raw:
            try:
                activities = json.loads(activities_raw) if isinstance(activities_raw, str) else activities_raw
                if not activities:
                    return Response(
                        {
                            "error": "Activities list cannot be empty.",
                            "activities": activities,
                        },
                        status=400
                    )
                data["activities"] = activities
            except json.JSONDecodeError:
                return Response({"error": "Invalid activities JSON"}, status=400)

        # Now pass to serializer
        serializer = EventSerializer(event, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)



    def delete(self, request, slug):
        event = self.get_object(slug)
        if not event:
            return Response({"error": "Not found"}, status=404)
        event.delete()
        return Response(status=204)



# -------- Activity Views --------
class ActivityAdminView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        serializer = ActivitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(event=event)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# -------- EventForm Views --------
class EventFormCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EventFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Form submitted successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventFormListAdminView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, slug):
        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        forms = EventForm.objects.filter(event=event).order_by("-submitted_at")
        serializer = EventFormSerializer(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class S3DocumentManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    # authentication_classes = [CustomJWTAuthentication]
    # permission_classes = [IsAdminUser]
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Upload an image to a folder.
        Example: POST with 'image' in form-data, optional 'folder'
        """
        image_file = request.FILES.get('image')
        folder = request.data.get('folder', 'cover')

        if not image_file:
            return Response({'error': 'No image file provided'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = upload_image_to_s3(image_file=image_file, folder=folder, bucket=bucket)

        if not response['error']:
            print('Response message:', response['message'], 'url:', response['url'])
            return Response({'message': response['message'], 'url': response['url'], 'key': response['key']}, status=200)
        
        if response['error']:
            print('Response error message:', response['message'])
            return Response({'message': response['message']}, status=400)
        

    def delete(self, request):
        """
        Delete an image from S3.
        Example: DELETE /api/s3-image/?key=cover/image.jpg
        """
        image_key = request.query_params.get('key')

        if not image_key:
            return Response({'error': 'Image key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME

        response = delete_image_from_s3(bucket=bucket, image_key=image_key)

        if not response['error']:
            print('Response message:', response['message'], image_key)
            return Response({'message':response['message']}, status=200)
        
        if response['error']:
            print('Response error message:', response['message'])
            return Response({'message':response['message']}, status=400)
        

class S3ImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def post(self, request):
        """
        Upload an image to a folder.
        Example: POST with 'image' in form-data, optional 'folder'
        """
        image_file = request.FILES.get('image')
        folder = request.data.get('folder', 'cover')

        if not image_file:
            return Response({'error': 'No image file provided'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME
        response = upload_image_to_s3(image_file=image_file, folder=folder, bucket=bucket)

        if not response['error']:
            print('Response message:', response['message'], 'url:', response['url'])
            return Response({'message': response['message'], 'url': response['url'], 'key': response['key']}, status=200)
        
        if response['error']:
            print('Response error message:', response['message'])
            return Response({'message': response['message']}, status=400)
        

    def delete(self, request):
        """
        Delete an image from S3.
        Example: DELETE /api/s3-image/?key=cover/image.jpg
        """
        image_key = request.query_params.get('key')

        if not image_key:
            return Response({'error': 'Image key is required'}, status=400)

        bucket = S3_BLOG_BUCKET_NAME

        response = delete_image_from_s3(bucket=bucket, image_key=image_key)

        if not response['error']:
            print('Response message:', response['message'], image_key)
            return Response({'message':response['message']}, status=200)
        
        if response['error']:
            print('Response error message:', response['message'])
            return Response({'message':response['message']}, status=400)
        

class PartnersListCreateView(APIView):
    def get(self, request):
        partners = Partners.objects.all()
        serializer = PartnersSerializer(partners, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = PartnersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerDetailView(APIView):
    def get(self, request, pk):
        partner = get_object_or_404(Partners, pk=pk)
        serializer = PartnersSerializer(partner)
        return Response(serializer.data, status=status.HTTP_200_OK)

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        partner = get_object_or_404(Partners, pk=pk)
        serializer = PartnersSerializer(partner, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        partner = get_object_or_404(Partners, pk=pk)
        partner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
