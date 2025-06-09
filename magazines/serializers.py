# magazines/serializers.py

from rest_framework import serializers
from .models import MagazineTag, Magazine, FeaturedPerson

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
            'pdf_url', 'pdf_key', 'show_on_home', 'on_home_priority', 'tags', 'tag_ids',
            'created_at', 'updated_at',
        ]


class FeaturedPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedPerson
        fields = [
            'id', 'magazine', 'title', 'short_description', 'long_description',
            'job_title', 'job_abbreviation',
            'image_url', 'image_key',
            'linkedin_link', 'x_link', 'facebook_link', 'instagram_link',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeaturedPersonDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedPerson
        fields = '__all__'

# Short serializer (for list fetch, excludes long_description)
class FeaturedPersonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedPerson
        exclude = ['long_description']