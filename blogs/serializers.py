# blog/serializers.py

from rest_framework import serializers
from .models import BlogTag, Blog

class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'content',
            'cover_image', 'blog_frame_image',  # ✅ Include it here
            'tags', 'is_published', 'priority',
            'created_at', 'updated_at', 'author', 'user',
        ]
        read_only_fields = ['user']
        extra_kwargs = {
            'tags': {'required': False}  # allow empty tags
        }

