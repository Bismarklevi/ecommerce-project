from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("event_type", "user", "channel", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "event_type")
    search_fields = ("user__username", "subject")
    readonly_fields = ("created_at", "sent_at")
