# contributors/models.py

from django.db import models

class TopContributor(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255, blank=True, null=True)
    job = models.CharField(max_length=255)
    job_abbreviation = models.CharField(max_length=50, blank=True)
    priority = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', '-created_at']

    def __str__(self):
        return self.name
