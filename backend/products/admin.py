from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Product, ProductImage, ProductVariant, Review


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "thumbnail", "alt_text", "credit", "position")
    readonly_fields = ("thumbnail",)

    @admin.display(description="Preview")
    def thumbnail(self, obj):
        if not obj or not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:4px;" />',
            obj.image.url,
        )


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class StockLevelFilter(admin.SimpleListFilter):
    title = "stock level"
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return [
            ("out", "Out of stock (0)"),
            ("low", "Low stock (1–5)"),
            ("healthy", "In stock (6+)"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "out":
            return queryset.filter(stock_quantity=0)
        if self.value() == "low":
            return queryset.filter(stock_quantity__gt=0, stock_quantity__lte=5)
        if self.value() == "healthy":
            return queryset.filter(stock_quantity__gt=5)
        return queryset


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    """The business-facing "Inventory" page -- every variant across every
    product in one sortable, filterable, stock-editable list, rather than
    only reachable one product at a time via the inline on ProductAdmin."""

    list_display = ("product", "sku", "size", "color", "stock_quantity", "price", "stock_status")
    list_display_links = ("product", "sku")
    list_editable = ("stock_quantity",)
    list_filter = (StockLevelFilter, "product__category")
    search_fields = ("sku", "product__name")
    ordering = ("stock_quantity",)
    list_select_related = ("product", "product__category")

    @admin.display(description="Status")
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return "Out of stock"
        if obj.stock_quantity <= 5:
            return "Low stock"
        return "In stock"


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("thumbnail", "name", "slug", "is_active", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("preview",)
    fields = (
        "name", "slug", "description",
        "image", "image_url", "image_credit", "preview",
        "is_active",
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        url = obj.image.url if obj.image else obj.image_url
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="height:36px;width:56px;object-fit:cover;border-radius:4px;" />', url,
        )

    @admin.display(description="Preview")
    def preview(self, obj):
        url = obj.image.url if obj.image else obj.image_url
        if not url:
            return "No image set yet -- upload one above, or paste a static URL."
        return format_html(
            '<img src="{}" style="max-height:220px;max-width:100%;object-fit:contain;'
            'border-radius:8px;border:1px solid #ccc;" />', url,
        )


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "category", "base_price", "is_featured", "is_active", "stock_status", "updated_at")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]

    @admin.display(description="Stock")
    def stock_status(self, obj):
        total = sum(v.stock_quantity for v in obj.variants.all())
        if total == 0:
            return "Out of stock"
        if total <= 5:
            return f"Low ({total})"
        return f"In stock ({total})"


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("product", "user", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved")
    search_fields = ("product__name", "user__username", "title", "body")
    actions = ["approve_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} review(s) approved.")
