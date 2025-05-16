# blog/serializers.py

from rest_framework import serializers
from .models import BlogTag, Blog

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
            'tags', 'tag_ids',  # show full tags, accept tag IDs
            'is_published', 'priority',
            'created_at', 'updated_at', 'author', 'user', 'views'
        ]
        read_only_fields = ['user', 'slug']

