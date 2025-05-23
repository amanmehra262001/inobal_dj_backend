# serializers.py
from rest_framework import serializers
from .models import Podcast, PodcastTag

class PodcastTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PodcastTag
        fields = ['id', 'name', 'slug']

class PodcastSerializer(serializers.ModelSerializer):
    tags = PodcastTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=PodcastTag.objects.all(),
        write_only=True,
        many=True,
        source='tags'
    )

    class Meta:
        model = Podcast
        fields = [
            'id', 'title', 'description', 'transcript',
            'views', 'duration', 'published_date',
            'audio_url', 'audio_key', 'cover_image_url', 'cover_image_key',
            'is_published', 'priority',
            'tags', 'tag_ids'
        ]



class PodcastListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Podcast
        exclude = ['transcript']  # Or use `fields` without transcript

