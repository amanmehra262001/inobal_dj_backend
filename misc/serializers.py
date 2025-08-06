from rest_framework import serializers
from .models import Career, BlogNotification, Advertisement, Activity, Event, EventForm, Partners, PartnerBannerImage, PartnerAward
import json
from rest_framework.utils import model_meta

class CareerSerializer(serializers.ModelSerializer):
    work_mode_display = serializers.SerializerMethodField()

    class Meta:
        model = Career
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_work_mode_display(self, obj):
        return obj.get_work_mode_display()


class BlogNotificationSerializer(serializers.ModelSerializer):
    blog_title = serializers.CharField(source='blog.title', read_only=True)
    blog_id = serializers.IntegerField(source='blog.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BlogNotification
        fields = [
            'id',
            'status',
            'status_display',
            'is_read',
            'created_at',
            'blog_id',
            'blog_title',
        ]

class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['event']


class EventSerializer(serializers.ModelSerializer):
    activities = ActivitySerializer(many=True, required=False)

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['slug']

    def create(self, validated_data):
        activities_data = validated_data.pop('activities', [])
        event = Event.objects.create(**validated_data)

        for activity_data in activities_data:
            Activity.objects.create(event=event, **activity_data)

        return event

    def update(self, instance, validated_data):
        print("validated_data before popping activities:", validated_data)
        activities_data = validated_data.pop('activities', None)

        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if activities_data is not None:
            instance.activities.all().delete()  # Clear old activities
            for activity_data in activities_data:
                Activity.objects.create(event=instance, **activity_data)

        return instance


class EventFormSerializer(serializers.ModelSerializer):
    event = serializers.SlugRelatedField(
        queryset=Event.objects.all(),
        slug_field="slug"
    )
    
    class Meta:
        model = EventForm
        fields = '__all__'
        read_only_fields = ['submitted_at']


class PartnerBannerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerBannerImage
        fields = ['id', 'image_url', 'image_key']


class PartnerAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerAward
        fields = ['id', 'title', 'award_url']


class PartnersSerializer(serializers.ModelSerializer):
    banner_images = PartnerBannerImageSerializer(many=True, required=False)
    awards = PartnerAwardSerializer(many=True, required=False)

    class Meta:
        model = Partners
        fields = [
            'id',
            'name',
            'short_head',
            'short_description',
            'long_description',
            'logo_image_url',
            'logo_image_key',
            'partner_website_link',
            'banner_images',
            'awards',
        ]

    def to_internal_value(self, data):
        data = data.copy()

        for field in ['banner_images', 'awards']:
            if isinstance(data.get(field), str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    raise serializers.ValidationError({field: "Invalid JSON format."})

        internal = super().to_internal_value(data)

        # Manually validate nested fields
        if 'banner_images' in data:
            banner_serializer = PartnerBannerImageSerializer(data=data['banner_images'], many=True)
            banner_serializer.is_valid(raise_exception=True)
            internal['banner_images'] = banner_serializer.validated_data

        if 'awards' in data:
            award_serializer = PartnerAwardSerializer(data=data['awards'], many=True)
            award_serializer.is_valid(raise_exception=True)
            internal['awards'] = award_serializer.validated_data

        return internal

    def create(self, validated_data):
        banner_images_data = validated_data.pop('banner_images', [])
        awards_data = validated_data.pop('awards', [])

        partner = Partners.objects.create(**validated_data)

        for img_data in banner_images_data:
            PartnerBannerImage.objects.create(partner=partner, **img_data)

        for award_data in awards_data:
            PartnerAward.objects.create(partner=partner, **award_data)

        return partner

    def update(self, instance, validated_data):
        banner_images_data = validated_data.pop('banner_images', None)
        awards_data = validated_data.pop('awards', None)

        # Update partner fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if banner_images_data is not None:
            instance.banner_images.all().delete()
            for img_data in banner_images_data:
                PartnerBannerImage.objects.create(partner=instance, **img_data)

        if awards_data is not None:
            instance.awards.all().delete()
            for award_data in awards_data:
                PartnerAward.objects.create(partner=instance, **award_data)

        return instance
