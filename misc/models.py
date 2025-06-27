from django.db import models

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
