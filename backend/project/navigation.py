"""Business-oriented Unfold sidebar (Phase 2/3/10 of the dashboard brief):
grouped around what a store owner does (Orders, Products, Marketing...)
rather than the app/model list Django's default admin auto-generates.

Every link below resolves to a real, already-registered admin view --
nothing here is a placeholder. Where the brief asked for a nav item with no
exact model behind it (Campaigns, Refunds, Store Settings), it's mapped to
the closest real existing view rather than invented; see the inline notes
and DASHBOARD_CHANGELOG.md for the full list of those calls.

Technical/system administration (auth tokens, permission groups, raw saved
addresses) is kept in its own "System" group, gated to superusers only via
`permission`, rather than removed -- Phase 3 explicitly says these models
must stay reachable for staff who need them, just not front-and-center for
a business owner.
"""
from django.urls import reverse


def _is_superuser(request):
    return request.user.is_active and request.user.is_superuser


def get_navigation(request):
    def url(name, **kwargs):
        try:
            return reverse(name, kwargs=kwargs or None)
        except Exception:
            return None

    return [
        {
            "title": "",
            "items": [
                {"title": "Dashboard", "icon": "dashboard", "link": reverse("admin:index")},
            ],
        },
        {
            "title": "Orders",
            "items": [
                {"title": "All orders", "icon": "receipt_long", "link": url("admin:app_order_changelist")},
                # Cart doesn't have an explicit "abandoned" flag -- CartAdmin
                # adds a real list_filter for it (idle 24h+ with items still
                # in it), so this links to that filtered view rather than a
                # page that doesn't exist.
                {
                    "title": "Abandoned carts", "icon": "remove_shopping_cart",
                    "link": f"{url('admin:app_cart_changelist')}?abandoned=yes",
                },
                {"title": "Returns", "icon": "assignment_return", "link": url("admin:returns_returnrequest_changelist")},
            ],
        },
        {
            "title": "Products",
            "items": [
                {"title": "Products", "icon": "checkroom", "link": url("admin:products_product_changelist")},
                {"title": "Categories", "icon": "category", "link": url("admin:products_category_changelist")},
                {"title": "Inventory", "icon": "inventory_2", "link": url("admin:products_productvariant_changelist")},
                {"title": "Reviews", "icon": "star_rate", "link": url("admin:products_review_changelist")},
            ],
        },
        {
            "title": "Customers",
            "items": [
                {"title": "Customers", "icon": "people", "link": url("admin:users_user_changelist")},
            ],
        },
        {
            "title": "Marketing",
            "items": [
                {"title": "Coupons", "icon": "sell", "link": url("admin:promotions_coupon_changelist")},
                # No separate Campaign model exists in this codebase --
                # Banners (time-boxed homepage promotions) are the closest
                # real analog, so "Campaigns" and "Banners" both point at
                # the same real page rather than inventing a second model
                # for what both requests actually mean here.
                {"title": "Banners & campaigns", "icon": "campaign", "link": url("admin:cms_banner_changelist")},
                {"title": "Site content", "icon": "article", "link": url("admin:cms_contentblock_changelist")},
            ],
        },
        {
            "title": "Shipping",
            "items": [
                {"title": "Shipping zones", "icon": "local_shipping", "link": url("admin:shipping_shippingzone_changelist")},
            ],
        },
        {
            "title": "Finance",
            "items": [
                {"title": "Payments", "icon": "payments", "link": url("admin:app_payment_changelist")},
                # No standalone Refund model -- a refund is a Payment in the
                # "refunded" state (see app.models.Payment.STATUS_REFUNDED).
                # Real filtered view, not a placeholder page.
                {
                    "title": "Refunds", "icon": "currency_exchange",
                    "link": f"{url('admin:app_payment_changelist')}?status__exact=refunded",
                },
            ],
        },
        {
            "title": "Analytics",
            "items": [
                # The dashboard itself *is* the sales/product/customer
                # analytics view (Sections 4/6/10 of the brief all live
                # there) -- a second, separate analytics page would just
                # duplicate it, which Phase 1 explicitly says not to do.
                {"title": "Sales & performance", "icon": "monitoring", "link": reverse("admin:index")},
            ],
        },
        {
            "title": "Settings",
            "items": [
                # No settings-in-database model exists yet (store info,
                # payment/shipping config are currently environment
                # variables -- see backend/.env.example). Site content
                # (banners' surrounding copy, editable blocks) is the one
                # part of "store settings" that already has a real admin
                # page; that's what this links to rather than a page that
                # isn't there. Payment/shipping *configuration* screens are
                # a genuine gap -- flagged in DASHBOARD_CHANGELOG.md, not
                # faked here.
                {"title": "Site content", "icon": "settings", "link": url("admin:cms_contentblock_changelist")},
                {
                    "title": "Staff & permissions", "icon": "admin_panel_settings",
                    "link": f"{url('admin:users_user_changelist')}?is_staff__exact=1",
                    "permission": _is_superuser,
                },
            ],
        },
        {
            "title": "System",
            "permission": _is_superuser,
            "items": [
                {"title": "Auth tokens", "icon": "vpn_key", "link": url("admin:authtoken_tokenproxy_changelist"), "permission": _is_superuser},
                {"title": "Permission groups", "icon": "shield", "link": url("admin:auth_group_changelist"), "permission": _is_superuser},
                {"title": "Saved addresses", "icon": "home_pin", "link": url("admin:users_address_changelist"), "permission": _is_superuser},
            ],
        },
    ]
