from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from user.models import UserAuth
from rest_framework.permissions import BasePermission
from common.constants import AUTH_TYPE_ADMIN, AUTH_TYPE_USER, AUTH_TYPE_SUBSCRIBER

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get("user_id")
            auth_type = validated_token.get("auth_type")

            if user_id is None:
                raise exceptions.AuthenticationFailed("Token contained no recognizable user identification")

            user = UserAuth.objects.get(id=user_id)
            user.auth_type_from_token = auth_type

            # Ensure flags are synced
            if user.is_staff:
                user.auth_role = AUTH_TYPE_ADMIN
            elif user.is_subscriber:
                user.auth_role = AUTH_TYPE_SUBSCRIBER
            else:
                user.auth_role = AUTH_TYPE_USER

            return user

        except UserAuth.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")
        

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsSubscriberUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, "is_subscriber", False)
        )
