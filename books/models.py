from django.db import models
from django.utils.text import slugify


class BookTag(models.Model):  # Same as PodcastTag
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name = "Book Tag"
        verbose_name_plural = "Book Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    published_date = models.DateField()
    affiliate_link = models.URLField(blank=True, null=True)

    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255, blank=True, null=True)

    tags = models.ManyToManyField(BookTag, related_name="books", blank=True)
    views = models.PositiveIntegerField(default=0)
    priority = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', '-published_date']

    def __str__(self):
        return self.title


class BooksHomeImages(models.Model):
    image_url = models.URLField(blank=True, null=True)
    image_key = models.CharField(max_length=255, blank=True, null=True)
    priority = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.image_key
