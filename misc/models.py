from django.db import models
from user.models import UserAuth
from blogs.models import Blog
from django.core.exceptions import ValidationError


class Career(models.Model):
    WORK_MODES = [
        ('remote', 'Remote'),
        ('in_office', 'In-Office'),
        ('hybrid', 'Hybrid'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    work_mode = models.CharField(max_length=20, choices=WORK_MODES, default='remote')
    form_link = models.URLField(help_text="Link to the application form (e.g. Typeform, Google Form)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.PositiveIntegerField(default=0, help_text="Lower number = higher priority")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', '-created_at']
        verbose_name = "Career Opportunity"
        verbose_name_plural = "Career Opportunities"

    def __str__(self):
        return f"{self.title} ({self.get_work_mode_display()})"


class BlogNotification(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Your article has been successfully uploaded! - Check it out.'),
        ('pending', 'Your blog is awaiting admin approval.'),
        ('rejected', 'Your blog has been rejected!'),
    ]

    user = models.ForeignKey(UserAuth, on_delete=models.CASCADE, related_name='blog_notifications')
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='notifications')  # if you have a Blog model
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Notification"
        verbose_name_plural = "Blog Notifications"

    def __str__(self):
        return f"{self.user.email} - {self.get_status_display()}"


class Advertisement(models.Model):
    ORIENTATION_CHOICES = [
        ('horizontal', 'Horizontal'),
        ('vertical', 'Vertical'),
    ]

    orientation = models.CharField(
        max_length=10,
        choices=ORIENTATION_CHOICES,
        unique=True,  # ensures only one entry per orientation
    )
    image_url = models.URLField()
    image_key = models.CharField(max_length=255)
    form_link = models.URLField()

    def clean(self):
        # Enforce only one entry per orientation at a time
        if Advertisement.objects.exclude(pk=self.pk).count() >= 2:
            raise ValidationError("Only two advertisement entries (horizontal & vertical) are allowed.")

    def save(self, *args, **kwargs):
        self.full_clean()  # trigger validation on save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.orientation.title()} Ad"

class Event(models.Model):
    title = models.CharField(max_length=255)
    short_description = models.TextField(max_length=300)
    long_description = models.TextField()
    date = models.DateField()
    is_published = models.BooleanField(default=False)

    cover_image = models.ImageField(upload_to='events/covers/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='events/banners/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Activity(models.Model):
    event = models.ForeignKey(Event, related_name="activities", on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.TextField()

    def __str__(self):
        return f"{self.description[:50]} ({self.start_time} - {self.end_time})"


class EventForm(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    event = models.ForeignKey('Event', related_name='submissions', on_delete=models.CASCADE)
    
    company_name = models.CharField(max_length=200, blank=True, null=True)
    title_at_company = models.CharField(max_length=150, blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event.title}"