from rest_framework import serializers
from .models import UserProfile, OmnisendContacts

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'image_url', 'image_key', 'occupation', 'bio']


class OmnisendContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OmnisendContacts
        fields = [
            "id",
            "email",
            "omnisend_id",
            "created_at",
            "updated_at",
            "is_contacted", 
            "is_subscribed", 
            "note",

        ]
        read_only_fields = ["id", "omnisend_id", "created_at", "updated_at"]


class OmnisendContactsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OmnisendContacts
        fields = ["is_contacted", "is_subscribed", "note"]
