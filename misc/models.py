from django.db import models
from user.models import UserAuth
from blogs.models import Blog

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
