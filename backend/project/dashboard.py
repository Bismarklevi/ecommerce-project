"""Feeds Unfold's admin dashboard with numbers a store operator actually needs to
act on today, rather than a generic 'X objects' count per model.

All the actual querying lives in analytics/services.py (shared with the
/api/analytics/sales/ endpoint) -- this module's job is just to call those
functions, shape the results for project/templates/admin/index.html, and stay
resilient (Phase 14: one broken metric must never take down the whole page).
"""
import logging

from django.urls import reverse
from django.utils import timezone

from analytics import services

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 5


def _greeting(hour: int) -> str:
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _safe(fn, default, *args, **kwargs):
    """Runs one dashboard metric in isolation -- if it raises, the rest of the
    dashboard still renders (Phase 14) and the real error goes to the server
    log, never to the page."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        logger.exception("Dashboard metric %s failed", getattr(fn, "__name__", fn))
        return default


def _orders_to_fulfill_count() -> int:
    from app.models import Order

    return Order.objects.filter(status__in=[Order.STATUS_PAID, Order.STATUS_PROCESSING]).count()


def _pending_reviews_count() -> int:
    from products.models import Review

    return Review.objects.filter(is_approved=False).count()


def dashboard_callback(request, context):
    now = timezone.localtime()
    admin_name = ""
    if request.user.is_authenticated:
        admin_name = request.user.get_full_name() or request.user.get_username()

    primary = _safe(
        services.primary_kpis,
        {
            "revenue_today": 0, "revenue_change": None, "orders_today": 0, "orders_change": None,
            "average_order_value": 0, "new_customers_today": 0, "new_customers_change": None,
        },
    )

    orders_to_fulfill = _safe(_orders_to_fulfill_count, 0)
    inventory = _safe(
        services.inventory_health,
        {"total_products": 0, "total_variants": 0, "in_stock": 0, "low_stock": 0, "out_of_stock": 0},
    )
    pending_reviews = _safe(_pending_reviews_count, 0)
    pending_returns = _safe(services.pending_returns_count, 0)
    abandoned_carts = _safe(services.abandoned_cart_count, 0)

    # Sales Overview period filter: a real query param + full page render per
    # period (rather than fragile client-side JS reaching into Unfold's
    # chart lifecycle, which only initializes once on load) -- still "real
    # data, no hardcoding", just server-driven instead of client-driven.
    period = request.GET.get("period", "30d")
    if period not in ("7d", "30d", "3m", "12m"):
        period = "30d"
    chart = _safe(services.sales_chart_series, {"labels": [], "revenue": [], "orders": [], "period": period}, period=period)

    operational = [
        {
            "title": "Orders to fulfill", "value": orders_to_fulfill, "footnote": "Paid or processing",
            "tone": "red" if orders_to_fulfill else "green", "url": _url("app_order_changelist"),
        },
        {
            "title": "Low stock", "value": inventory["low_stock"], "footnote": f"\u2264 {LOW_STOCK_THRESHOLD} units left",
            "tone": "amber" if inventory["low_stock"] else "green", "url": _url("products_productvariant_changelist"),
        },
        {
            "title": "Out of stock", "value": inventory["out_of_stock"], "footnote": "Unavailable to customers",
            "tone": "red" if inventory["out_of_stock"] else "green", "url": _url("products_productvariant_changelist"),
        },
        {
            "title": "Pending reviews", "value": pending_reviews, "footnote": "Awaiting moderation",
            "tone": "amber" if pending_reviews else "green", "url": _url("products_review_changelist"),
        },
        {
            "title": "Pending returns", "value": pending_returns, "footnote": "Needs a decision",
            "tone": "amber" if pending_returns else "green", "url": _url("returns_returnrequest_changelist"),
        },
    ]

    # "Needs your attention" reuses the same numbers as the operational KPI
    # row above (Phase 1: don't compute the same thing twice) -- it's just a
    # different presentation (actionable list vs. cards), plus abandoned carts.
    attention_items = []
    if orders_to_fulfill:
        attention_items.append({
            "icon": "\U0001F534", "text": f"{orders_to_fulfill} order{'s' if orders_to_fulfill != 1 else ''} awaiting fulfillment",
            "footnote": "Action needed", "url": _url("app_order_changelist"), "label": "View orders",
        })
    if inventory["low_stock"]:
        attention_items.append({
            "icon": "\U0001F534", "text": f"{inventory['low_stock']} product variant{'s' if inventory['low_stock'] != 1 else ''} low in stock",
            "footnote": "Reorder soon", "url": _url("products_productvariant_changelist"), "label": "View inventory",
        })
    if pending_returns:
        attention_items.append({
            "icon": "\U0001F7E0", "text": f"{pending_returns} return request{'s' if pending_returns != 1 else ''} awaiting review",
            "footnote": "Customer is waiting", "url": _url("returns_returnrequest_changelist"), "label": "Review returns",
        })
    if pending_reviews:
        attention_items.append({
            "icon": "\U0001F7E1", "text": f"{pending_reviews} review{'s' if pending_reviews != 1 else ''} awaiting moderation",
            "footnote": "Not yet public", "url": _url("products_review_changelist"), "label": "Moderate",
        })
    if abandoned_carts:
        attention_items.append({
            "icon": "\U0001F7E1", "text": f"{abandoned_carts} abandoned cart{'s' if abandoned_carts != 1 else ''}",
            "footnote": "Inactive 24h+ with items", "url": _url("app_cart_changelist"), "label": "View carts",
        })

    context.update({
        "kaira_greeting": _greeting(now.hour),
        "kaira_admin_name": admin_name,
        "kaira_today": now,
        "kaira_primary_kpis": primary,
        "kaira_operational_kpis": operational,
        "kaira_attention_items": attention_items,
        "kaira_top_products": _safe(services.top_selling_products, []),
        "kaira_inventory": inventory,
        "kaira_low_stock_rows": _safe(services.low_stock_variants, []),
        "kaira_low_stock_threshold": LOW_STOCK_THRESHOLD,
        "kaira_recent_orders": _safe(services.recent_orders, []),
        "kaira_customers": _safe(
            services.customer_overview,
            {"total_customers": 0, "new_customers": 0, "returning_customers": 0, "repeat_purchase_rate": 0},
        ),
        "kaira_chart": chart,
        "kaira_chart_json": _chart_json(chart),
        "kaira_chart_periods": [
            {"value": "7d", "label": "7 Days", "url": _period_url(request, "7d")},
            {"value": "30d", "label": "30 Days", "url": _period_url(request, "30d")},
            {"value": "3m", "label": "3 Months", "url": _period_url(request, "3m")},
            {"value": "12m", "label": "12 Months", "url": _period_url(request, "12m")},
        ],
        "kaira_quick_actions": [
            {"label": "Add product", "url": _url("products_product_add")},
            {"label": "Create promotion", "url": _url("promotions_coupon_add")},
            {"label": "View orders", "url": _url("app_order_changelist")},
            {"label": "View inventory", "url": _url("products_productvariant_changelist")},
            {"label": "View customers", "url": _url("users_user_changelist")},
            {"label": "Review returns", "url": _url("returns_returnrequest_changelist")},
        ],
    })
    return context


def _url(admin_url_name: str) -> str:
    try:
        return reverse(f"admin:{admin_url_name}")
    except Exception:
        return ""


def _period_url(request, period: str) -> str:
    return f"{request.path}?period={period}"


def _chart_json(chart: dict) -> str:
    """Shapes the service layer's {labels, revenue, orders} into the
    {labels, datasets} structure Unfold's bundled Chart.js component expects
    (see unfold/templates/unfold/components/chart/line.html) -- kept as a
    separate step so services.sales_chart_series() itself stays a plain,
    presentation-agnostic data function."""
    import json

    return json.dumps({
        "labels": chart["labels"],
        "datasets": [
            {
                "label": "Revenue (GH\u20b5)",
                "data": chart["revenue"],
                "borderColor": "var(--color-primary-600)",
                "backgroundColor": "var(--color-primary-600)",
                "tension": 0.3,
            },
            {
                "label": "Orders",
                "data": chart["orders"],
                "borderColor": "var(--color-base-400)",
                "backgroundColor": "var(--color-base-400)",
                "tension": 0.3,
                "yAxisID": "y1",
            },
        ],
    })
