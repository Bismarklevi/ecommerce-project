from django.core.management.base import BaseCommand
from django.utils.text import slugify

from app.image_generation import render_clothing_image
from products.models import Category, Product, ProductImage, ProductVariant


class Command(BaseCommand):
    help = "Seed sample catalog data for the storefront"

    def add_arguments(self, parser):
        parser.add_argument(
            "--regenerate-images",
            action="store_true",
            help="Replace existing product images with freshly generated studio assets.",
        )

    def handle(self, *args, **options):
        regenerate_images = options["regenerate_images"]
        category, _ = Category.objects.get_or_create(
            name="Clothing",
            defaults={
                "description": "Modern everyday essentials for relaxed style.",
                "slug": "clothing",
            },
        )

        products = [
            {
                "name": "Linen Overshirt",
                "short_description": "Lightweight layering piece for warm days.",
                "description": "A relaxed overshirt crafted for comfort, texture, and easy styling.",
                "price": "89.00",
                "is_featured": True,
                "variants": [
                    {"sku": "LINEN-OVERSHIRT-S-SAND", "size": "S", "color": "Sand", "stock_quantity": 8, "price": "89.00", "is_default": True},
                    {"sku": "LINEN-OVERSHIRT-M-SAND", "size": "M", "color": "Sand", "stock_quantity": 12, "price": "89.00", "is_default": False},
                ],
            },
            {
                "name": "Relaxed Denim Jacket",
                "short_description": "Structured outerwear with a soft hand feel.",
                "description": "A utility-inspired denim jacket built for transitional weather and repeat wear.",
                "price": "119.00",
                "is_featured": True,
                "variants": [
                    {"sku": "DENIM-JACKET-M-INDIGO", "size": "M", "color": "Indigo", "stock_quantity": 5, "price": "119.00", "is_default": True},
                    {"sku": "DENIM-JACKET-L-INDIGO", "size": "L", "color": "Indigo", "stock_quantity": 4, "price": "119.00", "is_default": False},
                ],
            },
        ]

        for product_payload in products:
            product, created = Product.objects.get_or_create(
                name=product_payload["name"],
                defaults={
                    "category": category,
                    "short_description": product_payload["short_description"],
                    "description": product_payload["description"],
                    "base_price": product_payload["price"],
                    "is_featured": product_payload["is_featured"],
                    "slug": slugify(product_payload["name"]),
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))

            for variant_payload in product_payload["variants"]:
                variant, variant_created = ProductVariant.objects.get_or_create(
                    product=product,
                    sku=variant_payload["sku"],
                    defaults={
                        "size": variant_payload["size"],
                        "color": variant_payload["color"],
                        "stock_quantity": variant_payload["stock_quantity"],
                        "price": variant_payload["price"],
                        "is_default": variant_payload["is_default"],
                    },
                )

                if variant_created:
                    self.stdout.write(self.style.SUCCESS(f"Created variant: {variant.sku}"))

            existing_images = list(product.images.all())
            if regenerate_images:
                for existing_image in existing_images:
                    if existing_image.image:
                        existing_image.image.delete(save=False)
                    existing_image.delete()
                existing_images = []

            if not existing_images:
                image_file = render_clothing_image(product.name, product.short_description or product.description)
                ProductImage.objects.create(
                    product=product,
                    alt_text=product.name,
                    position=1,
                    image=image_file,
                )

                self.stdout.write(self.style.SUCCESS(f"Created studio image for {product.name}"))
