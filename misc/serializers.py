from rest_framework import serializers
from .models import Career, BlogNotification, Advertisement, Activity, Event, EventForm

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
