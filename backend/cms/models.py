from django.db import models
from django.utils import timezone


class Banner(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="cms/banners/")
    link_url = models.CharField(max_length=300, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_currently_visible(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True


class ContentBlock(models.Model):
    """A named, editable chunk of homepage/marketing copy — e.g. 'homepage_hero_text'
    or 'shipping_policy_summary' — so copy changes don't require a deploy."""

    key = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key
