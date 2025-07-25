from rest_framework import serializers
from .models import Book, BookTag, BooksHomeImages, BooksHomeDetails


class BookTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTag
        fields = ['id', 'name', 'slug']


class BookSerializer(serializers.ModelSerializer):
    tags = BookTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=BookTag.objects.all(), write_only=True, many=True, required=False
    )

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author_name',
            'description',
            'published_date',
            'affiliate_link',
            'image_url',
            'image_key',
            'views',
            'priority',
            'is_published',
            'tags',
            'tag_ids',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        tags = validated_data.pop("tag_ids", [])
        book = Book.objects.create(**validated_data)
        book.tags.set(tags)
        return book

    def update(self, instance, validated_data):
        tags = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class BooksHomeImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BooksHomeImages
        fields = ['id', 'image_url', 'image_key', 'priority', 'created_at', 'updated_at']

    def create(self, validated_data):
        return BooksHomeImages.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class BooksHomeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BooksHomeDetails
        fields = '__all__'