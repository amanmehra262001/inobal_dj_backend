from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from rest_framework import status, permissions
import traceback
from user.models import UserAuth, AdminProfile, UserProfile, SubscriberProfile, OmnisendContacts
import uuid
from common.constants import AUTH_TYPE_GOOGLE, AUTH_TYPE_EMAIL, AUTH_TYPE_ADMIN, AUTH_TYPE_USER, AUTH_TYPE_SUBSCRIBER
from django.contrib.auth import authenticate
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from user.tokens import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.views import CustomJWTAuthentication, IsAdminUser, IsSubscriberUser
from user.serializers import UserProfileSerializer, OmnisendContactsSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from common.utils.s3_utils import upload_image_to_s3, delete_image_from_s3
from common.constants import S3_USER_BUCKET_NAME, S3_BLOG_BUCKET_NAME
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings


# Google Sign in functionality
class GoogleSigninView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Google token is required"}, status=status.HTTP_400_BAD_REQUEST)

        return self.handle_google_signin(token)

    def handle_google_signin(self, token):
        try:
            # Fetch user info from Google using access token
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token}"}
            try:
                response = requests.get(user_info_url, headers=headers, timeout=10)
            except requests.exceptions.RequestException as e:
                return Response({"error": "Failed to connect to Google"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            if response.status_code != 200:
                return Response({"error": "Failed to fetch user info from Google"}, status=status.HTTP_400_BAD_REQUEST)

            user_info = response.json()

            if not user_info.get('verified_email'):
                return Response({"error": "Email not verified by Google"}, status=status.HTTP_400_BAD_REQUEST)

            user, created = self.create_or_get_user(user_info)

            if not user:
                return Response({"error": "Error getting user"}, status=status.HTTP_400_BAD_REQUEST)
            
            print('user:', user)
            # Generate JWT tokens for the user
            refresh = RefreshToken.for_user(user)
            refresh['auth_type'] = AUTH_TYPE_USER
            
            user_details = {
                "user_id": user.id,
                "email": user.email,
                "access_token": str(refresh.access_token),
                "refresh": str(refresh)
            }

            return JsonResponse({**user_details, "message": "User Signed In"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            traceback.print_exc()
            return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def create_or_get_user(self, user_info):
        user_email = user_info.get('email', '')
        try:
            # Check if user with this email already exists
            user = UserAuth.objects.get(email=user_email)

            # If the user exists, return it
            return user, False

        except UserAuth.DoesNotExist:
            try:
                # If the user does not exist, create a new one
                unique_id = f"google_{uuid.uuid4().hex[:8]}"  # Generate a unique ID for the new user
                user = UserAuth.objects.create(
                    email=user_email,
                    auth_type=AUTH_TYPE_GOOGLE,
                    unique_id=unique_id,  # Ensure unique ID is set
                )
                return user, True

            except Exception as err:
                print('Error creating new user:', err)
                return None, False

        except Exception as e:
            print('Error fetching user:', e)
            return None, False


# Sign up functionality

class EmailPasswordSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Get the email and password from the request data
        email = request.data.get('email')
        password = request.data.get('password')
        is_subscriber = request.data.get('is_subscriber')
        print('email:', email)
        print('password:', password)
        print('is_subscriber:', is_subscriber)

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        if UserAuth.objects.filter(email=email).exists():
            return Response({"error": "Email is already taken"}, status=status.HTTP_400_BAD_REQUEST)

         # Generate a unique_id for the user (can be UUID, or use another method)
        unique_id = f"email_{uuid.uuid4().hex[:8]}"  # Generates a unique UUID as the unique_id

        # Create the user
        try:
            user = UserAuth.objects.create_user(
                email=email,
                password=password,
                auth_type=AUTH_TYPE_EMAIL,
                unique_id=unique_id,  # Ensure to pass the unique_id
                is_subscriber=True if is_subscriber else False
            )

            # Generate JWT tokens for the user
            refresh = RefreshToken.for_user(user)
            
            # Send back the response with user details and JWT tokens
            user_details = {
                "user_id": user.id,
                "email": user.email,
                "access_token": str(refresh.access_token),
                "refresh": str(refresh)
            }

            return Response({**user_details, "message": "User created successfully"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print('Error:', str(e))
            traceback.print_exc()
            return Response({"error": "Something went wrong during user creation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Login functionality

class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            # Look up the user by email
            user = UserAuth.objects.get(email=email)
            if user and check_password(password, user.password):
                return user
        except UserAuth.DoesNotExist:
            return None

        return None

class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Get the email and password from the request data
        email = request.data.get('email')
        password = request.data.get('password')
        print('email:', email)
        print('password:', password)

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Use the custom EmailAuthBackend to authenticate the user
        user = EmailAuthBackend().authenticate(request, email=email, password=password)

        if user is None:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user is active
        if not user.is_active:
            return Response({"error": "User is inactive"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT tokens for the authenticated user
        refresh = RefreshToken.for_user(user)
        refresh['auth_type'] = AUTH_TYPE_USER

        if user.is_subscriber:
            refresh['auth_type'] = AUTH_TYPE_SUBSCRIBER
        
        # Send back the response with user details and JWT tokens
        user_details = {
            "user_id": user.id,
            "email": user.email,
            "access_token": str(refresh.access_token),
            "refresh": str(refresh)
        }

        return Response({**user_details, "message": "Login successful"}, status=status.HTTP_200_OK)



# admin user login views
class AdminAuthBackend(BaseBackend):
    def authenticate(self, request, unique_id=None, password=None):
        try:
            # Look up the user by email
            user = UserAuth.objects.get(unique_id=unique_id)
            print('user:', user)
            if user and check_password(password, user.password):
                print('user:', user)
                return user
        except UserAuth.DoesNotExist:
            return None

        return None
    
class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("admin login post view")
        unique_id = request.data.get('unique_id')
        password = request.data.get('password')
        print('unique id and pass:', unique_id, password)

        if not unique_id or not password:
            return Response({"error": "Unique ID and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = AdminAuthBackend().authenticate(request, unique_id=unique_id, password=password)

        if user is None or not user.is_staff:
            return Response({"error": "Invalid credentials or not an admin"}, status=status.HTTP_401_UNAUTHORIZED)

        admin_profile = AdminProfile.objects.get(user=user)

        refresh = RefreshToken.for_user(user)
        refresh['auth_type'] = AUTH_TYPE_ADMIN

        return Response({
            "user_id": user.id,
            "unique_id": user.unique_id,
            "name": admin_profile.full_name,
            "email": user.email,
            "access_token": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Admin login successful"
        }, status=status.HTTP_200_OK)


# view for jwt tokens
class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class AuthenticatedUserView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # --- Default response values ---
        response_data = {
            "user_id": user.id,
            "email": getattr(user, "email", ""),
            "unique_id": getattr(user, "unique_id", ""),
            "auth_type": None,
            "name": "",
            "image_key": "",
            "image_url": "",
            "occupation": "",
            "bio": "",
            "subscription_start": None,
            "subscription_end": None,
            "subscription_plan": None,
            "message": "Authenticated user info fetched successfully"
        }

        # --- Admin case ---
        if user.is_staff:
            admin_profile = AdminProfile.objects.filter(user=user).first()
            if not admin_profile:
                return Response({"error": "Admin profile not found"}, status=status.HTTP_400_BAD_REQUEST)

            response_data.update({
                "name": admin_profile.full_name,
                "auth_type": AUTH_TYPE_ADMIN
            })
            return Response(response_data, status=status.HTTP_200_OK)

        # --- Non-admin (User / Subscriber / Both) ---
        user_profile = UserProfile.objects.filter(user=user).first()
        subscriber_profile = SubscriberProfile.objects.filter(user=user).first()

        has_user_profile = bool(user_profile)
        has_subscriber_profile = bool(subscriber_profile)

        if not has_user_profile and not has_subscriber_profile:
            return Response({
                "error": "No profile (User or Subscriber) found for this account"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fill UserProfile data if exists
        if user_profile:
            response_data.update({
                "name": user_profile.name,
                "image_url": user_profile.image_url or "",
                "image_key": user_profile.image_key or "",
                "occupation": user_profile.occupation or "",
                "bio": user_profile.bio or "",
            })

        # Fill SubscriberProfile data if exists
        if subscriber_profile:
            # Prefer subscriber full_name if no user profile exists
            if not user_profile:
                response_data["name"] = subscriber_profile.full_name

            response_data.update({
                "subscription_start": subscriber_profile.subscription_start,
                "subscription_end": subscriber_profile.subscription_end,
                "subscription_plan": subscriber_profile.subscription_plan,
            })

        # Decide auth_type
        if has_user_profile and has_subscriber_profile:
            response_data["auth_type"] = AUTH_TYPE_SUBSCRIBER
        elif has_subscriber_profile:
            response_data["auth_type"] = AUTH_TYPE_SUBSCRIBER
        elif has_user_profile:
            response_data["auth_type"] = AUTH_TYPE_USER

        return Response(response_data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        if hasattr(request.user, 'profile'):
            return Response({"detail": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class S3UserImageManager(APIView):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

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


class GetAllUsersView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    class CustomPagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'
        max_page_size = 100

    def get(self, request, *args, **kwargs):
        # Check if the authenticated user is an admin
        if not request.user.is_staff:
            return Response(
                {"error": "Access denied. Admin privileges required."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Check if email is provided for single user lookup
            email = request.query_params.get('email')
            
            if email:
                # Get single user details
                return self.get_single_user(email)
            else:
                # Get all users with pagination
                return self.get_all_users(request)

        except Exception as e:
            print('Error in GetAllUsersView:', e)
            return Response({
                "error": "Failed to retrieve user(s)"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Create a new user"""
        # Check if the authenticated user is an admin
        if not request.user.is_staff:
            return Response(
                {"error": "Access denied. Admin privileges required."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Extract user data from request
            email = request.data.get('email')
            password = request.data.get('password')
            unique_id = request.data.get('unique_id')
            is_subscriber = request.data.get('is_subscriber', False)
            auth_type = request.data.get('auth_type', AUTH_TYPE_EMAIL)
            subscription_plan = request.data.get('subscription_plan', 'Basic')
            subscription_end = request.data.get('subscription_end', None)
            subscription_start = request.data.get('subscription_start', None)
            occupation = request.data.get('occupation', '')
            bio = request.data.get('bio', '')
            subscriber_name = request.data.get('subscriber_name', email.split('@')[0])
            user_name = request.data.get('user_name', email.split('@')[0])

            # Validate required fields
            if not email or not password:
                return Response({
                    "error": "Email and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if email already exists
            if UserAuth.objects.filter(email=email).exists():
                return Response({
                    "error": "Email is already taken"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate unique_id if not provided
            if not unique_id:
                unique_id = f"email_{uuid.uuid4().hex[:8]}"

            # Create the user
            user = UserAuth.objects.create_user(
                email=email,
                password=password,
                unique_id=unique_id,
                auth_type=auth_type,
                is_subscriber=is_subscriber,
            )

            # Create profile based on user type
            if is_subscriber:
                SubscriberProfile.objects.create(
                    user=user,
                    full_name=subscriber_name,
                    subscription_plan=subscription_plan,
                    subscription_start=subscription_start,
                    subscription_end=subscription_end
                )
            else:
                UserProfile.objects.create(
                    user=user,
                    name=user_name,
                    occupation=occupation,
                    bio=bio
                )

            return Response({
                "message": "User created successfully",
                "email": user.email,
                "unique_id": user.unique_id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print('Error creating user:', e)
            return Response({
                "error": "Failed to create user"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """Update an existing user"""
        # Check if the authenticated user is an admin
        if not request.user.is_staff:
            return Response(
                {"error": "Access denied. Admin privileges required."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Get email from query params
            email = request.query_params.get('email')
            if not email:
                return Response({
                    "error": "email is required for updating a user"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find the user
            try:
                user = UserAuth.objects.get(email=email)
            except UserAuth.DoesNotExist:
                return Response({
                    "error": f"User with email '{email}' not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Update basic user fields
            if 'email' in request.data and request.data['email'] != user.email:
                # Check if new email is already taken
                if UserAuth.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
                    return Response({
                        "error": "Email is already taken by another user"
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.email = request.data['email']

            if 'unique_id' in request.data and request.data['unique_id'] != user.unique_id:
                # Check if new unique_id is already taken
                if UserAuth.objects.filter(unique_id=request.data['unique_id']).exclude(id=user.id).exists():
                    return Response({
                        "error": "Unique ID is already taken by another user"
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.unique_id = request.data['unique_id']

            if 'is_subscriber' in request.data:
                user.is_subscriber = request.data['is_subscriber']
            if 'is_active' in request.data:
                user.is_active = request.data['is_active']
            if 'is_verified' in request.data:
                user.is_verified = request.data['is_verified']
            if 'auth_type' in request.data:
                user.auth_type = request.data['auth_type']

            # Update password if provided
            if 'password' in request.data and request.data['password']:
                user.set_password(request.data['password'])

            user.save()

            # Update or create profiles based on user type
            if user.is_subscriber:
                subscriber_profile, created = SubscriberProfile.objects.get_or_create(user=user)
                if 'subscriber_name' in request.data:
                    subscriber_profile.full_name = request.data['subscriber_name']
                if 'subscription_plan' in request.data:
                    subscriber_profile.subscription_plan = request.data['subscription_plan']
                if 'subscription_start' in request.data:
                    subscriber_profile.subscription_start = request.data['subscription_start']
                if 'subscription_end' in request.data:
                    subscriber_profile.subscription_end = request.data['subscription_end']
                if 'active' in request.data:
                    subscriber_profile.active = request.data['active']
                subscriber_profile.save()
            else:
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                if 'user_name' in request.data:
                    user_profile.name = request.data['user_name']
                if 'occupation' in request.data:
                    user_profile.occupation = request.data['occupation']
                if 'bio' in request.data:
                    user_profile.bio = request.data['bio']
                user_profile.save()

            return Response({
                "message": "User updated successfully",
                "email": user.email,
                "unique_id": user.unique_id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print('Error updating user:', e)
            return Response({
                "error": "Failed to update user"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_single_user(self, email):
        """Get detailed information for a single user"""
        try:
            # Try to get user by ID first
            try:
                user = UserAuth.objects.get(email=email)
            except UserAuth.DoesNotExist:
                return Response({
                    "error": f"User with email '{email}' not found"
                }, status=status.HTTP_404_NOT_FOUND)

            user_data = {
                "email": user.email,
                "unique_id": user.unique_id,
                "is_staff": user.is_staff,
                "is_subscriber": user.is_subscriber,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "auth_type": user.auth_type,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "profiles": {}
            }
            
            # Get UserProfile if exists
            try:
                user_profile = UserProfile.objects.get(user=user)
                user_data["profiles"]["user_profile"] = {
                    "name": user_profile.name,
                    "image_url": user_profile.image_url,
                    "image_key": user_profile.image_key,
                    "occupation": user_profile.occupation,
                    "bio": user_profile.bio
                }
            except UserProfile.DoesNotExist:
                user_data["profiles"]["user_profile"] = None
            
            # Get SubscriberProfile if exists
            try:
                subscriber_profile = SubscriberProfile.objects.get(user=user)
                user_data["profiles"]["subscriber_profile"] = {
                    "full_name": subscriber_profile.full_name,
                    "subscription_plan": subscriber_profile.subscription_plan,
                    "subscription_start": subscriber_profile.subscription_start,
                    "subscription_end": subscriber_profile.subscription_end,
                    "active": subscriber_profile.active
                }
            except SubscriberProfile.DoesNotExist:
                user_data["profiles"]["subscriber_profile"] = None
            
            # Get AdminProfile if exists
            try:
                admin_profile = AdminProfile.objects.get(user=user)
                user_data["profiles"]["admin_profile"] = {
                    "full_name": admin_profile.full_name,
                    "joined_on": admin_profile.joined_on,
                    "active": admin_profile.active
                }
            except AdminProfile.DoesNotExist:
                user_data["profiles"]["admin_profile"] = None
            
            # Determine the primary profile type
            if user.is_staff:
                user_data["primary_profile"] = "admin"
            elif user.is_subscriber:
                user_data["primary_profile"] = "subscriber"
            else:
                user_data["primary_profile"] = "user"

            return Response({
                "user": user_data,
                "message": f"User details retrieved successfully for {user.email or user.unique_id}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print('Error fetching single user:', e)
            return Response({
                "error": "Failed to retrieve user details"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_all_users(self, request):
        """Get all users with pagination"""
        try:
            # Get all users from UserAuth
            users_queryset = UserAuth.objects.all().order_by('-date_joined')
            
            users_data = []
            
            for user in users_queryset:
                user_data = {
                    "email": user.email,
                    "unique_id": user.unique_id,
                    "is_staff": user.is_staff,
                    "is_subscriber": user.is_subscriber,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "is_superuser": user.is_superuser,
                    "auth_type": user.auth_type,
                    "date_joined": user.date_joined,
                    "last_login": user.last_login,
                    "profiles": {}
                }
                
                # Get UserProfile if exists
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_data["profiles"]["user_profile"] = {
                        "name": user_profile.name,
                        "image_url": user_profile.image_url,
                        "image_key": user_profile.image_key,
                        "occupation": user_profile.occupation,
                        "bio": user_profile.bio
                    }
                except UserProfile.DoesNotExist:
                    user_data["profiles"]["user_profile"] = None
                
                # Get SubscriberProfile if exists
                try:
                    subscriber_profile = SubscriberProfile.objects.get(user=user)
                    user_data["profiles"]["subscriber_profile"] = {
                        "full_name": subscriber_profile.full_name,
                        "subscription_plan": subscriber_profile.subscription_plan,
                        "subscription_start": subscriber_profile.subscription_start,
                        "subscription_end": subscriber_profile.subscription_end,
                        "active": subscriber_profile.active
                    }
                except SubscriberProfile.DoesNotExist:
                    user_data["profiles"]["subscriber_profile"] = None
                
                # Get AdminProfile if exists
                try:
                    admin_profile = AdminProfile.objects.get(user=user)
                    user_data["profiles"]["admin_profile"] = {
                        "full_name": admin_profile.full_name,
                        "joined_on": admin_profile.joined_on,
                        "active": admin_profile.active
                    }
                except AdminProfile.DoesNotExist:
                    user_data["profiles"]["admin_profile"] = None
                
                # Determine the primary profile type
                if user.is_staff:
                    user_data["primary_profile"] = "admin"
                elif user.is_subscriber:
                    user_data["primary_profile"] = "subscriber"
                else:
                    user_data["primary_profile"] = "user"
                
                users_data.append(user_data)
            
            # Use custom pagination
            paginator = self.CustomPagination()
            result_page = paginator.paginate_queryset(users_data, request)
            
            return paginator.get_paginated_response(result_page)

        except Exception as e:
            print('Error fetching all users:', e)
            return Response({
                "error": "Failed to retrieve users"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetUserSubscriptionDetails(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsSubscriberUser]

    def get(self, request, *args, **kwargs):
        """
        Fetch subscription details for the currently authenticated user.
        """
        user = request.user

        # Ensure the user is actually a subscriber
        if not user.is_subscriber:
            return Response({
                "error": "This user does not have a subscription."
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            subscriber_profile = SubscriberProfile.objects.get(user=user)
        except SubscriberProfile.DoesNotExist:
            return Response({
                "error": "Subscriber profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize subscription details
        subscription_details = {
            "subscriber_name": subscriber_profile.full_name,
            "subscription_plan": subscriber_profile.subscription_plan,
            "subscription_start": subscriber_profile.subscription_start,
            "subscription_end": subscriber_profile.subscription_end,
            "active": subscriber_profile.active,
        }

        return Response(subscription_details, status=status.HTTP_200_OK)


OMNISEND_BASE_URL = "https://api.omnisend.com/v5/contacts"
OMNISEND_API_KEY = settings.OMNISEND_API_KEY
class OmnisendContactsView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def get_permissions(self):
        """
        Public: POST
        Admin only: GET, PUT
        """
        if self.request.method == "POST":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @staticmethod
    def create_omnisend_contact(email: str, custom_properties: dict = None, status: str = "nonSubscribed"):
        """
        Creates a contact in Omnisend via API.
        Returns dict {"success": True, "data": {...}} on success
        or {"success": False, "error": "message"} on failure.
        """
        if not OMNISEND_API_KEY:
            return {"success": False, "error": "Omnisend API key not configured."}

        headers = {
            "X-API-KEY": OMNISEND_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }

        payload = {
            "customProperties": custom_properties or {},
            "identifiers": [
                {
                    "channels": {
                        "email": {
                            "status": status
                        }
                    },
                    "type": "email",
                    "id": email
                }
            ]
        }

        try:
            response = requests.post(OMNISEND_BASE_URL, json=payload, headers=headers, timeout=10)

            if response.status_code == 201:
                return {"success": True, "data": response.json()}

            elif response.status_code == 409:
                # Already exists — return response anyway
                return {"success": True, "data": response.json()}

            else:
                return {
                    "success": False,
                    "error": f"Omnisend API error {response.status_code}: {response.text}"
                }

        except requests.Timeout:
            return {"success": False, "error": "Omnisend API request timed out."}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    # Public POST: subscribe user
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        contact, created = OmnisendContacts.objects.get_or_create(email=email)

        omni_response = self.create_omnisend_contact(email=email, status="subscribed")

        if omni_response["success"]:
            data = omni_response["data"]
            contact.omnisend_id = data.get("contactID", contact.omnisend_id)
            contact.is_subscribed = True
            contact.save()
        else:
            # Do not fail user signup just because Omnisend failed
            return Response(
                {"detail": "Contact saved locally, but Omnisend sync failed.", "error": omni_response["error"]},
                status=status.HTTP_202_ACCEPTED
            )

        serializer = OmnisendContactsSerializer(contact)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # Admin GET: list contacts
    def get(self, request):
        contacts = OmnisendContacts.objects.all().order_by("-created_at")
        serializer = OmnisendContactsSerializer(contacts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    # # Admin PUT: update contact
    # def put(self, request):
    #     contact_id = request.data.get("id")
    #     if not contact_id:
    #         return Response({"detail": "Contact ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         contact = OmnisendContacts.objects.get(id=contact_id)
    #     except OmnisendContacts.DoesNotExist:
    #         return Response({"detail": "Contact not found"}, status=status.HTTP_404_NOT_FOUND)

    #     serializer = OmnisendContactsSerializer(contact, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
