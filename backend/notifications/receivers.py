from .services import notify_order_status_change


def handle_order_status_changed(sender, order, previous_status, new_status, **kwargs):
    notify_order_status_change(order, new_status)
