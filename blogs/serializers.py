# blog/serializers.py

from rest_framework import serializers
from .models import BlogTag, Blog
from common.constants import AUTH_TYPE_ADMIN

class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class BlogSerializer(serializers.ModelSerializer):
    tags = BlogTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=BlogTag.objects.all(), write_only=True, many=True, source='tags'
    )

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'description', 'slug', 'content',
            'cover_image', 'blog_frame_image',
            'tags', 'tag_ids', 'published_date',
            'is_published', 'priority', 'views',
            'is_rejected', 'created_at', 'updated_at', 'author', 'user'
        ]
        read_only_fields = ['user', 'slug']

    def update(self, instance, validated_data):
        user = self.context['request'].user

        # Prevent normal users from updating restricted fields
        if getattr(user, 'auth_type_from_token', None) != AUTH_TYPE_ADMIN:
            for field in ['views', 'priority', 'is_published', 'is_rejected', 'published_date']:
                validated_data.pop(field, None)

        return super().update(instance, validated_data)

    def create(self, validated_data):
        user = self.context['request'].user

        # Prevent normal users from setting restricted fields
        if getattr(user, 'auth_type_from_token', None) != AUTH_TYPE_ADMIN:
            for field in ['views', 'priority', 'is_published', 'is_rejected', 'published_date']:
                validated_data.pop(field, None)

        return super().create(validated_data)


class BlogListSerializer(serializers.ModelSerializer):
    tags = BlogTagSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        exclude = ['content']  # 🚫 Exclude content from list
