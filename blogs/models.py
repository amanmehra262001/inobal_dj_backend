from django.db import models
from django.utils.text import slugify
import itertools
from user.models import UserAuth

class BlogTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name = "Blog Tag"
        verbose_name_plural = "Blog Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatically generate slug from name
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Blog(models.Model):
    user = models.ForeignKey(  # Link to UserAuth model
        UserAuth,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blogs'
    )
    author = models.CharField(  # Display name of the author
        max_length=255,
        blank=True,
        null=True
    )
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=270, unique=True, blank=True)
    content = models.JSONField(default=list)  # store structured content
    views = models.IntegerField(default=0)
    description = models.CharField(max_length=300, blank=True)
    
    cover_image = models.URLField(blank=True, null=True)
    blog_frame_image = models.URLField(blank=True, null=True)
    
    tags = models.ManyToManyField('BlogTag', related_name="blogs", blank=True)

    is_published = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)

    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            for i in itertools.count(1):
                if not Blog.objects.filter(slug=slug).exists():
                    break
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)
