from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ReturnRequest


def _make_transition_action(target_status, label):
    def action(modeladmin, request, queryset):
        succeeded, failed = 0, []
        for return_request in queryset:
            try:
                return_request.transition_to(target_status)
                succeeded += 1
            except ValueError as exc:
                failed.append(str(exc))
        if succeeded:
            modeladmin.message_user(request, f"{succeeded} return request(s) moved to '{target_status}'.")
        for message in failed:
            modeladmin.message_user(request, message, level="warning")

    action.short_description = label
    action.__name__ = f"mark_{target_status}"
    return action


@admin.register(ReturnRequest)
class ReturnRequestAdmin(ModelAdmin):
    list_display = ("order", "status", "refund_amount", "created_at")
    list_filter = ("status",)
    search_fields = ("order__id", "order__user__username", "reason")
    readonly_fields = ("status", "created_at", "updated_at")
    actions = [
        _make_transition_action(ReturnRequest.STATUS_APPROVED, "Approve selected return requests"),
        _make_transition_action(ReturnRequest.STATUS_REJECTED, "Reject selected return requests"),
        _make_transition_action(ReturnRequest.STATUS_REFUNDED, "Mark selected return requests as refunded"),
    ]
