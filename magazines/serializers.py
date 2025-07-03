# magazines/serializers.py

from rest_framework import serializers
from .models import MagazineTag, Magazine, FeaturedPerson, MagazinePage

class MagazineTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagazineTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class MagazinePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagazinePage
        fields = ['page_number', 'image_url', 'image_key']


class MagazineSerializer(serializers.ModelSerializer):
    tags = MagazineTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=MagazineTag.objects.all(), write_only=True, many=True, source='tags'
    )
    pages = MagazinePageSerializer(many=True, required=False)

    class Meta:
        model = Magazine
        fields = [
            'id', 'name', 'description', 'published_date',
            'is_published', 'views',
            'cover_image_url', 'cover_image_key',
            'show_on_home', 'on_home_priority', 'tags', 'tag_ids',
            'pages',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        pages_data = validated_data.pop('pages', [])
        tags = validated_data.pop('tags', [])

        magazine = Magazine.objects.create(**validated_data)
        magazine.tags.set(tags)

        for page in pages_data:
            MagazinePage.objects.create(magazine=magazine, **page)

        return magazine

    def update(self, instance, validated_data):
        pages_data = validated_data.pop('pages', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if pages_data is not None:
            # clear and recreate all pages (or implement smarter diff logic)
            instance.pages.all().delete()
            for page in pages_data:
                MagazinePage.objects.create(magazine=instance, **page)

        return instance


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