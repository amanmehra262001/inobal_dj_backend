from rest_framework import serializers
from .models import Career, BlogNotification, Advertisement, Activity, Event, EventForm, Partners, PartnerBannerImage, PartnerAward, EventDay, EventMetric
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
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Activity
        fields = [
            "id",
            "order",
            "short_description",
            "description",
            "start_time",
            "end_time",
        ]


class EventDaySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    activities = ActivitySerializer(many=True)

    class Meta:
        model = EventDay
        fields = [
            "id",
            "order",
            "date",
            "start_time",
            "end_time",
            "activities",
        ]

class EventMetricSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EventMetric
        fields = ["id", "label", "value", "suffix", "icon", "order", "is_highlight"]

class EventSerializer(serializers.ModelSerializer):
    days = EventDaySerializer(many=True)
    metrics = EventMetricSerializer(many=True, required=False)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "long_description",
            "event_date",
            "start_time",
            "end_time",
            "timezone",
            "location",
            "event_type",
            "is_published",
            "cover_image_url",
            "cover_image_key",
            "banner_image_url",
            "banner_image_key",
            "days",
            "metrics",
        ]
        read_only_fields = ["slug"]

    def create(self, validated_data):
        days_data = validated_data.pop("days", [])
        metrics_data = validated_data.pop("metrics", [])
        event = Event.objects.create(**validated_data)

        for day_data in days_data:
            activities_data = day_data.pop("activities", [])
            day = EventDay.objects.create(event=event, **day_data)

            for activity_data in activities_data:
                Activity.objects.create(day=day, **activity_data)
        
        for metric in metrics_data:
            EventMetric.objects.create(event=event, **metric)

        return event
    
    def update(self, instance, validated_data):
        days_data = validated_data.pop("days", [])
        metrics_data = validated_data.pop("metrics", [])

        existing_metrics = {m.id: m for m in instance.metrics.all()}

        for metric_data in metrics_data:
            metric_id = metric_data.get("id")

            if metric_id and metric_id in existing_metrics:
                metric = existing_metrics.pop(metric_id)
                for attr, value in metric_data.items():
                    setattr(metric, attr, value)
                metric.save()
            else:
                EventMetric.objects.create(event=instance, **metric_data)

        # delete: existing metrics removed
        for metric in existing_metrics.values():
            metric.delete()

        # Update Event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_days = {day.id: day for day in instance.days.all()}

        for day_data in days_data:
            activities_data = day_data.pop("activities", [])
            day_id = day_data.get("id", None)

            # UPDATE existing day
            if day_id and day_id in existing_days:
                day = existing_days.pop(day_id)

                for attr, value in day_data.items():
                    setattr(day, attr, value)
                day.save()

            # CREATE new day
            else:
                day = EventDay.objects.create(event=instance, **day_data)

            # --- Activities ---
            existing_activities = {a.id: a for a in day.activities.all()}

            for activity_data in activities_data:
                activity_id = activity_data.get("id", None)

                if activity_id and activity_id in existing_activities:
                    activity = existing_activities.pop(activity_id)

                    for attr, value in activity_data.items():
                        setattr(activity, attr, value)
                    activity.save()

                else:
                    Activity.objects.create(day=day, **activity_data)

            # DELETE removed activities
            for activity in existing_activities.values():
                activity.delete()

        # DELETE removed days
        for day in existing_days.values():
            day.delete()

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


class EventGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventGallery
        fields = [
            "id",
            "image_url",
            "image_key",
            "order",
            "caption",
            "created_at",
        ]
        

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
