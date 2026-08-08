from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import Order, OrderItem, Payment
from app.services import mark_order_paid
from products.models import Category, Product, ProductVariant

User = get_user_model()


def make_variant(stock=20, price="100.00", sku="SKU-DASH-1"):
    category = Category.objects.create(name="Dresses", slug="dresses")
    product = Product.objects.create(
        category=category, name="Test Dress", description="d", base_price=Decimal(price)
    )
    return ProductVariant.objects.create(
        product=product, sku=sku, size="M", color="Blue", stock_quantity=stock, price=Decimal(price),
    )


def make_paid_order(user, variant, quantity=1):
    order = Order.objects.create(user=user, total_amount=variant.price * quantity, shipping_name=user.username)
    OrderItem.objects.create(
        order=order, product_variant=variant, product_name=variant.product.name, product_sku=variant.sku,
        size=variant.size, color=variant.color, quantity=quantity,
        unit_price=variant.price, line_total=variant.price * quantity,
    )
    payment = Payment.objects.create(order=order, reference=f"ref-{order.id}", amount=order.total_amount)
    mark_order_paid(order, payment)
    return order


class DashboardRenderTests(TestCase):
    """Covers Phase 16's explicit ask: the dashboard loads, doesn't crash, and
    a superuser sees what a business owner needs to see."""

    def setUp(self):
        self.admin = User.objects.create_superuser(username="owner", email="owner@example.com", password="pw")
        self.client.force_login(self.admin)

    def test_dashboard_loads_with_no_data_at_all(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("No sales yet", content)
        self.assertIn("All caught up", content)
        self.assertIn("Inventory looks healthy", content)
        self.assertIn("No orders yet", content)

    def test_dashboard_loads_with_real_data(self):
        variant = make_variant()
        make_paid_order(self.admin, variant, quantity=2)

        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Sales overview", content)
        self.assertIn("Recent orders", content)
        self.assertIn("GH\u20b5", content)

    def test_low_stock_variant_appears_in_low_stock_table_and_kpi(self):
        variant = make_variant(stock=3)
        response = self.client.get("/admin/")
        content = response.content.decode()
        self.assertIn("Low stock products", content)
        self.assertIn(variant.sku, content)

    def test_out_of_stock_variant_counted_correctly(self):
        make_variant(stock=0)
        response = self.client.get("/admin/")
        self.assertContains(response, "Out of stock")

    def test_all_four_chart_periods_render_without_error(self):
        for period in ("7d", "30d", "3m", "12m"):
            response = self.client.get(f"/admin/?period={period}")
            self.assertEqual(response.status_code, 200, f"period={period} failed")

    def test_invalid_period_falls_back_to_default_instead_of_erroring(self):
        response = self.client.get("/admin/?period=not-a-real-period")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_query_count_is_bounded(self):
        """Phase 8: not dozens/hundreds of queries. Seeds a handful of orders
        and variants and asserts the page doesn't scale linearly with data
        volume in an obviously N+1 way."""
        variant = make_variant()
        for _ in range(5):
            make_paid_order(self.admin, variant)

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.client.get("/admin/")
        self.assertLess(len(ctx.captured_queries), 35, "dashboard query count grew unexpectedly")


class DashboardPermissionTests(TestCase):
    """Phase 3/9: technical administration hidden from regular staff, visible
    to superusers; nobody's access is silently broken."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(username="root", email="root@example.com", password="pw")
        self.staff = User.objects.create_user(username="staffer", email="staffer@example.com", password="pw", is_staff=True)

    def test_superuser_sees_system_navigation(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        self.assertContains(response, "Auth tokens")

    def test_regular_staff_does_not_see_system_navigation(self):
        self.client.force_login(self.staff)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Auth tokens")

    def test_anonymous_user_is_redirected_not_shown_dashboard(self):
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 200)


class DashboardMetricsCorrectnessTests(TestCase):
    """Phase 7: metrics must reflect real, correctly-scoped data -- failed
    payments and cancelled orders must never inflate revenue."""

    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="buyer@example.com", password="pw")
        self.variant = make_variant()

    def test_failed_payment_excluded_from_revenue(self):
        from analytics.services import revenue_for_period

        order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))
        Payment.objects.create(
            order=order, reference="failed-ref", amount=Decimal("100.00"), status=Payment.STATUS_FAILED,
        )
        since = timezone.now() - timedelta(days=1)
        self.assertEqual(revenue_for_period(since), Decimal("0.00"))

    def test_successful_payment_counted_in_revenue(self):
        from analytics.services import revenue_for_period

        make_paid_order(self.user, self.variant)
        since = timezone.now() - timedelta(days=1)
        self.assertEqual(revenue_for_period(since), self.variant.price)

    def test_average_order_value_does_not_divide_by_zero(self):
        from analytics.services import primary_kpis

        result = primary_kpis()  # no orders exist at all
        self.assertEqual(result["average_order_value"], 0)

    def test_returning_customer_requires_more_than_one_paid_order(self):
        from analytics.services import customer_overview

        make_paid_order(self.user, self.variant)
        result = customer_overview()
        self.assertEqual(result["returning_customers"], 0)

        make_paid_order(self.user, self.variant)
        result = customer_overview()
        self.assertEqual(result["returning_customers"], 1)

    def test_inventory_health_counts_at_variant_level_not_product_level(self):
        from analytics.services import inventory_health

        # Same product, two variants: one healthy, one low -- product-level
        # counting would collapse this to "1 product", variant-level (what
        # the brief requires) must show 2 variants.
        ProductVariant.objects.create(
            product=self.variant.product, sku="SKU-DASH-2", size="L", color="Blue",
            stock_quantity=2, price=self.variant.price,
        )
        result = inventory_health()
        self.assertEqual(result["total_variants"], 2)
        self.assertEqual(result["low_stock"], 1)
