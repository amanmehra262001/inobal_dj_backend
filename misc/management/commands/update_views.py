import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from blogs.models import Blog
from books.models import Book
from magazines.models import Magazine
from podcasts.models import Podcast


class Command(BaseCommand):
    help = "Weekly update of views for Blog, Book, Magazine, and Podcast"

    def handle(self, *args, **kwargs):
        self.update_views(Blog.objects.all(), "Blog")
        self.update_views(Book.objects.all(), "Book")
        self.update_views(Magazine.objects.all(), "Magazine")
        self.update_views(Podcast.objects.all(), "Podcast")

    def update_views(self, queryset, model_name):
        updated_count = 0
        for obj in queryset:
            increment = self.calculate_increment(obj)
            obj.views += increment
            obj.save(update_fields=["views"])
            updated_count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated_count} {model_name} objects")
        )

    def calculate_increment(self, obj):
        """Algorithm for incrementing views"""
        base = random.randint(5, 30)
        priority_boost = obj.priority * 5 if hasattr(obj, "priority") else 0
        return base + priority_boost
