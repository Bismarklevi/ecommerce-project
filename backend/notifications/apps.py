from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # Import inside ready() to avoid the app-loading circular-import trap
        # (app.models imports at Django startup; this wiring must happen after
        # all app registries are populated).
        from app.models import order_status_changed

        from .receivers import handle_order_status_changed

        order_status_changed.connect(handle_order_status_changed, dispatch_uid="notifications_order_status")
