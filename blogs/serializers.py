# blog/serializers.py

from rest_framework import serializers
from .models import BlogTag, Blog

class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class BlogSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source='tag.name', read_only=True)

    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'tag', 'tag_name', 'created_at', 'updated_at']
