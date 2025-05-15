from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from user.models import UserAuth


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get("user_id")
            auth_type = validated_token.get("auth_type")
            if user_id is None:
                raise exceptions.AuthenticationFailed("Token contained no recognizable user identification")

            user = UserAuth.objects.get(id=user_id)
            user.auth_type_from_token = auth_type

            return user

        except UserAuth.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")
