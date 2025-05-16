# magazines/models.py

from django.db import models
from django.utils.text import slugify
import itertools

class MagazineTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name = "Magazine Tag"
        verbose_name_plural = "Magazine Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Magazine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    published_date = models.DateField()
    is_published = models.BooleanField(default=False)
    views = models.IntegerField(default=0)

    cover_image_url = models.URLField(blank=True, null=True)
    cover_image_key = models.CharField(max_length=255, blank=True, null=True)

    tags = models.ManyToManyField(MagazineTag, related_name='magazines', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.published_date.year}"
