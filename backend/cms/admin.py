from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import Banner, ContentBlock


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ("thumbnail", "title", "position", "is_active", "starts_at", "ends_at")
    list_filter = ("is_active",)
    ordering = ("position",)
    readonly_fields = ("preview",)
    fields = (
        "title", "subtitle", "image", "preview", "link_url",
        "position", "is_active", "starts_at", "ends_at",
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height:36px;width:56px;object-fit:cover;border-radius:4px;" />',
            obj.image.url,
        )

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.image:
            return "No image uploaded yet."
        return format_html(
            '<img src="{}" style="max-height:220px;max-width:100%;object-fit:contain;'
            'border-radius:8px;border:1px solid #ccc;" />',
            obj.image.url,
        )


@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ("key", "title", "is_active", "updated_at")
    search_fields = ("key", "title", "body")
