from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from app.models import Order, OrderItem, Payment


def sales_summary(days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    successful_payments = Payment.objects.filter(status=Payment.STATUS_SUCCESS, updated_at__gte=since)

    revenue = successful_payments.aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
    order_count = Order.objects.filter(
        payment_status=Order.PAYMENT_PAID, updated_at__gte=since
    ).count()

    return {
        "period_days": days,
        "revenue": revenue,
        "paid_order_count": order_count,
        "average_order_value": (revenue / order_count) if order_count else Decimal("0.00"),
    }


def top_selling_variants(days: int = 30, limit: int = 10) -> list[dict]:
    since = timezone.now() - timedelta(days=days)
    rows = (
        OrderItem.objects.filter(
            order__payment_status=Order.PAYMENT_PAID, order__updated_at__gte=since,
        )
        .values("product_sku", "product_name", "size", "color")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-units_sold")[:limit]
    )
    return list(rows)


def order_status_breakdown() -> list[dict]:
    return list(
        Order.objects.values("status").annotate(count=Count("id")).order_by("-count")
    )


# ---------------------------------------------------------------------------
# Dashboard-specific helpers below. Everything above this line predates the
# admin dashboard rebuild and is reused as-is (see top_selling_variants /
# sales_summary call sites) rather than duplicated.
# ---------------------------------------------------------------------------

ZERO_MONEY = Decimal("0.00")


def _money_sum(queryset, field: str) -> Decimal:
    """Sum() on an empty queryset returns None, not 0 -- this is the one place
    that gets normalized so every caller below can treat revenue as always a
    Decimal, never None."""
    return queryset.aggregate(
        total=Coalesce(Sum(field), Value(ZERO_MONEY, output_field=DecimalField()))
    )["total"]


def revenue_for_period(start, end=None) -> Decimal:
    """Revenue = successful payments in [start, end). Failed/pending payments and
    unpaid/cancelled orders are never counted -- see module docstring intent in
    dashboard_callback for why this definition was chosen over "order total"."""
    qs = Payment.objects.filter(status=Payment.STATUS_SUCCESS, updated_at__gte=start)
    if end is not None:
        qs = qs.filter(updated_at__lt=end)
    return _money_sum(qs, "amount")


def order_count_for_period(start, end=None) -> int:
    qs = Order.objects.filter(payment_status=Order.PAYMENT_PAID, updated_at__gte=start)
    if end is not None:
        qs = qs.filter(updated_at__lt=end)
    return qs.count()


def new_customers_for_period(start, end=None) -> int:
    from users.models import User

    qs = User.objects.filter(is_staff=False, date_joined__gte=start)
    if end is not None:
        qs = qs.filter(date_joined__lt=end)
    return qs.count()


def percent_change(current, previous) -> float | None:
    """None means "no baseline to compare against" (previous was 0) -- the
    template renders that as "—" rather than a misleading "+inf%"."""
    current = float(current)
    previous = float(previous)
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def primary_kpis() -> dict:
    """Today vs. yesterday, using calendar-day boundaries in the server's
    configured timezone (not just "last 24h"), which is what a store owner
    actually means by "today's sales"."""
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    today_revenue = revenue_for_period(today_start)
    yesterday_revenue = revenue_for_period(yesterday_start, today_start)

    today_orders = order_count_for_period(today_start)
    yesterday_orders = order_count_for_period(yesterday_start, today_start)

    today_customers = new_customers_for_period(today_start)
    yesterday_customers = new_customers_for_period(yesterday_start, today_start)

    return {
        "revenue_today": today_revenue,
        "revenue_change": percent_change(today_revenue, yesterday_revenue),
        "orders_today": today_orders,
        "orders_change": percent_change(today_orders, yesterday_orders),
        "average_order_value": (today_revenue / today_orders) if today_orders else ZERO_MONEY,
        "new_customers_today": today_customers,
        "new_customers_change": percent_change(today_customers, yesterday_customers),
    }


def abandoned_cart_count(hours: int = 24) -> int:
    """A cart counts as "abandoned" once it's had items sitting untouched for
    a while with no order to show for it -- there's no explicit "abandoned"
    flag on Cart, so this infers it from inactivity rather than adding a new
    field/migration for something derivable from existing data."""
    from app.models import Cart

    cutoff = timezone.now() - timedelta(hours=hours)
    return Cart.objects.filter(updated_at__lt=cutoff, items__isnull=False).distinct().count()


def pending_returns_count() -> int:
    from returns.models import ReturnRequest

    return ReturnRequest.objects.filter(status=ReturnRequest.STATUS_REQUESTED).count()


def inventory_health() -> dict:
    from products.models import Product, ProductVariant

    LOW_STOCK_THRESHOLD = 5
    variant_stats = ProductVariant.objects.aggregate(
        total_variants=Count("id"),
        in_stock=Count("id", filter=Q(stock_quantity__gt=LOW_STOCK_THRESHOLD)),
        low_stock=Count("id", filter=Q(stock_quantity__gt=0, stock_quantity__lte=LOW_STOCK_THRESHOLD)),
        out_of_stock=Count("id", filter=Q(stock_quantity=0)),
    )
    return {
        "total_products": Product.objects.filter(is_active=True).count(),
        "total_variants": variant_stats["total_variants"],
        "in_stock": variant_stats["in_stock"],
        "low_stock": variant_stats["low_stock"],
        "out_of_stock": variant_stats["out_of_stock"],
    }


def low_stock_variants(threshold: int = 5, limit: int = 8) -> list:
    from products.models import ProductVariant

    return list(
        ProductVariant.objects.filter(stock_quantity__lte=threshold, stock_quantity__gt=0)
        .select_related("product")
        .order_by("stock_quantity")[:limit]
    )


def top_selling_products(days: int = 30, limit: int = 5) -> list[dict]:
    """Product-level rollup (image/category/current stock), unlike
    top_selling_variants() above which stays at the SKU/size/color grain for
    the API's sales report. The dashboard card needs one row per product with
    a photo, so it re-aggregates one level up rather than overloading that
    function's existing contract."""
    from products.models import Product

    since = timezone.now() - timedelta(days=days)
    rows = (
        OrderItem.objects.filter(order__payment_status=Order.PAYMENT_PAID, order__updated_at__gte=since)
        .values("product_variant__product_id")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-units_sold")[:limit]
    )
    product_ids = [row["product_variant__product_id"] for row in rows]
    products_by_id = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids)
        .select_related("category")
        .prefetch_related("images", "variants")
    }

    results = []
    for row in rows:
        product = products_by_id.get(row["product_variant__product_id"])
        if not product:
            continue
        stock = sum(v.stock_quantity for v in product.variants.all())
        results.append(
            {
                "product": product,
                "units_sold": row["units_sold"],
                "revenue": row["revenue"] or ZERO_MONEY,
                "current_stock": stock,
                "status": "Out of stock" if stock == 0 else ("Low stock" if stock <= 5 else "In stock"),
            }
        )
    return results


def recent_orders(limit: int = 8) -> list:
    return list(
        Order.objects.select_related("user", "payment").order_by("-created_at")[:limit]
    )


def customer_overview(days: int = 30) -> dict:
    """"Returning" = has more than one paid order ever (not just in the window)
    -- a customer's second purchase still counts as "they came back" even if
    their first order was outside the reporting period."""
    from django.db.models import Count as CountAgg

    from users.models import User

    since = timezone.now() - timedelta(days=days)
    total_customers = User.objects.filter(is_staff=False).count()
    new_customers = User.objects.filter(is_staff=False, date_joined__gte=since).count()

    paid_order_counts = (
        Order.objects.filter(payment_status=Order.PAYMENT_PAID)
        .values("user_id")
        .annotate(order_count=CountAgg("id"))
    )
    customers_with_orders = len(paid_order_counts)
    returning_customers = sum(1 for row in paid_order_counts if row["order_count"] > 1)
    repeat_rate = (returning_customers / customers_with_orders * 100) if customers_with_orders else 0.0

    return {
        "total_customers": total_customers,
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "repeat_purchase_rate": round(repeat_rate, 1),
    }


def sales_chart_series(period: str = "30d") -> dict:
    """Daily revenue + order-count series for the requested period, with every
    date in range present (zero-filled) even if nothing sold that day -- a
    charting library fed a series with gaps silently misrenders the x-axis,
    so the zero-fill happens here rather than being every chart consumer's
    problem to remember."""
    period_days = {"7d": 7, "30d": 30, "3m": 90, "12m": 365}.get(period, 30)
    now = timezone.localtime()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=period_days - 1)

    rows = (
        Payment.objects.filter(status=Payment.STATUS_SUCCESS, updated_at__gte=start)
        .annotate(day=TruncDate("updated_at"))
        .values("day")
        .annotate(revenue=Sum("amount"), orders=Count("order_id", distinct=True))
        .order_by("day")
    )
    by_day = {row["day"]: row for row in rows}

    labels, revenue_series, order_series = [], [], []
    for i in range(period_days):
        day = (start + timedelta(days=i)).date()
        row = by_day.get(day)
        labels.append(day.strftime("%b %d"))
        revenue_series.append(float(row["revenue"]) if row else 0.0)
        order_series.append(row["orders"] if row else 0)

    return {"labels": labels, "revenue": revenue_series, "orders": order_series, "period": period}
