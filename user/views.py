from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from rest_framework import status
import traceback
from user.models import UserAuth
import uuid
from common.constants import AUTH_TYPE_GOOGLE, AUTH_TYPE_EMAIL
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password


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
