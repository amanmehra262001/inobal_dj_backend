from django.db import models
from django.utils.text import slugify


class PodcastTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name = "Podcast Tag"
        verbose_name_plural = "Podcast Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Podcast(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    views = models.PositiveIntegerField(default=0)
    duration = models.DurationField()  # e.g., "00:43:20"
    published_date = models.DateField()
    transcript = models.TextField(blank=True)

    audio_url = models.URLField(blank=True, null=True)
    audio_key = models.CharField(max_length=255, blank=True, null=True)

    cover_image_url = models.URLField(blank=True, null=True)
    cover_image_key = models.CharField(max_length=255, blank=True, null=True)

    spotify_embed_url = models.URLField(blank=True, null=True)  # New field for Spotify embed

    tags = models.ManyToManyField(PodcastTag, related_name="podcasts", blank=True)
    priority = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', '-published_date']

    def __str__(self):
        return self.title
