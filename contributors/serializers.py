# contributors/serializers.py

from rest_framework import serializers
from .models import TopContributor

class TopContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopContributor
        fields = [
            'id', 'name', 'short_description', 'long_description',
            'image_url', 'image_key', 'job', 'job_abbreviation', 'priority',
            'created_at'
        ]
