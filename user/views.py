from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from rest_framework import status
import traceback
from user.models import UserAuth, AdminProfile
import uuid
from common.constants import AUTH_TYPE_GOOGLE, AUTH_TYPE_EMAIL, AUTH_TYPE_ADMIN, AUTH_TYPE_USER
from django.contrib.auth import authenticate
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from user.tokens import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from common.views import CustomJWTAuthentication


# Google Sign in functionality

class GoogleSigninView(APIView):
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
            response = requests.get(user_info_url, headers=headers)

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
    def post(self, request, *args, **kwargs):
        # Get the email and password from the request data
        email = request.data.get('email')
        password = request.data.get('password')
        print('email:', email)
        print('password:', password)

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
                unique_id=unique_id  # Ensure to pass the unique_id
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
        auth_type = getattr(user, "auth_type", AUTH_TYPE_ADMIN if user.is_staff else AUTH_TYPE_USER)

        if auth_type == AUTH_TYPE_ADMIN:
            admin_profile = AdminProfile.objects.get(user=user)
            name = admin_profile.full_name

        # You can use the token claim 'auth_type' if needed
        return Response({
            "user_id": user.id,
            "email": getattr(user, "email", ""),
            "name": name or "",
            "unique_id": getattr(user, "unique_id", ""),
            "auth_type": auth_type,
            "message": "Authenticated user info fetched successfully"
        }, status=status.HTTP_200_OK)
