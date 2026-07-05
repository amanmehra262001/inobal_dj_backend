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

    show_on_home = models.BooleanField(default=False)
    on_home_priority = models.IntegerField(default=0)

    tags = models.ManyToManyField('MagazineTag', related_name='magazines', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.published_date.year}"

class MagazinePage(models.Model):
    magazine = models.ForeignKey(Magazine, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField()
    image_url = models.URLField()
    image_key = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']

    def __str__(self):
        return f"Magazine {self.magazine_id} - Page {self.page_number}"

class FeaturedPerson(models.Model):
    magazine = models.ForeignKey(
        Magazine,
        related_name='featured_people',
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    job_title = models.CharField(max_length=255)
    job_abbreviation = models.CharField(max_length=50, blank=True)

    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255, blank=True, null=True)

    linkedin_link = models.URLField(blank=True, null=True)
    x_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({self.job_abbreviation})"

    def save(self, *args, **kwargs):
        if self._state.adding and self.order == 0:
            last_order = (
                FeaturedPerson.objects
                .filter(magazine=self.magazine)
                .aggregate(Max("order"))["order__max"]
            )
            self.order = (last_order or 0) + 1

        super().save(*args, **kwargs)