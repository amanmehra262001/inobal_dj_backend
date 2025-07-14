from django.contrib import admin
from .models import Event, Activity, EventForm


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 1  # Number of empty activity forms to show by default
    fields = ('start_time', 'end_time', 'description')
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'is_published', 'created_at')
    list_filter = ('is_published', 'event_date')
    search_fields = ('title', 'short_description', 'long_description')
    inlines = [ActivityInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EventForm)
class EventFormAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'event', 'submitted_at')
    list_filter = ('event',)
    search_fields = ('full_name', 'professional_title_organization', 'email', 'phone_number')
    readonly_fields = ('submitted_at',)
