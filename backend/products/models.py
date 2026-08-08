from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="category_images/",
        blank=True,
        null=True,
        help_text="Hero/tile image shown on the homepage and category grid. Served through "
        "whichever storage backend is active in STORAGES (Cloudflare R2 in production).",
    )
    image_url = models.URLField(
        blank=True,
        help_text="Static fallback image URL (e.g. a direct Unsplash/Pexels link). Used when "
        "no file is uploaded to `image` -- lets you wire up real photos instantly without "
        "downloading/storing anything.",
    )
    image_credit = models.CharField(
        max_length=255,
        blank=True,
        help_text="Photographer/source attribution, e.g. 'Photo by Jane Doe on Unsplash'.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.order_by("position", "id").first()

    @property
    def display_price(self):
        return self.base_price

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=80, unique=True)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    stock_quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["size", "color"]

    @property
    def effective_price(self):
        return self.price or self.product.base_price

    def __str__(self):
        return f"{self.product.name} - {self.size} / {self.color}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    image_url = models.URLField(
        blank=True,
        help_text="Static fallback image URL (e.g. a direct Unsplash/Pexels link). Used when "
        "no file is uploaded to `image`.",
    )
    alt_text = models.CharField(max_length=200, blank=True)
    credit = models.CharField(
        max_length=255,
        blank=True,
        help_text="Photographer/source attribution, e.g. 'Photo by Jane Doe on Unsplash'.",
    )
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.alt_text or f"Image for {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_review_per_user_product",
            )
        ]

    def __str__(self):
        return f"{self.user.username} review on {self.product.name}"

