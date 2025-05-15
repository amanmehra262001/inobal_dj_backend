# tokens.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['user_id'] = user.id
        token['auth_type'] = user.auth_type  # this should be 'email', 'google', or 'admin'

        return token
