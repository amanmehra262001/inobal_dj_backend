# magazines/serializers.py

from rest_framework import serializers
from .models import MagazineTag, Magazine

class MagazineTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagazineTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class MagazineSerializer(serializers.ModelSerializer):
    tags = MagazineTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=MagazineTag.objects.all(), write_only=True, many=True, source='tags'
    )

    class Meta:
        model = Magazine
        fields = [
            'id', 'name', 'description', 'published_date',
            'is_published', 'views',
            'cover_image_url', 'cover_image_key',
            'pdf_url', 'pdf_key', 'tags', 'tag_ids',
            'created_at', 'updated_at',
        ]
