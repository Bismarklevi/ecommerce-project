from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from app.stock_photos import fetch_stock_photo
from products.models import Category, Product, ProductImage, ProductVariant

# One row per storefront category. `query` is what we search Unsplash/Pexels for --
# kept specific ("women's floral summer dress flatlay") rather than generic ("dress")
# so results actually look like the category instead of a random garment.
CATEGORIES = [
    {
        "name": "Dresses",
        "description": "Day dresses, occasion wear, and easy slip dresses for every season.",
        "query": "woman wearing summer dress fashion editorial",
    },
    {
        "name": "Tops & Blouses",
        "description": "Blouses, camisoles, and everyday tops that layer well.",
        "query": "woman wearing blouse fashion studio",
    },
    {
        "name": "Skirts",
        "description": "Midi, mini, and pleated skirts for work and weekends.",
        "query": "woman wearing midi skirt fashion",
    },
    {
        "name": "Jeans & Trousers",
        "description": "Denim and tailored trousers built for everyday wear.",
        "query": "woman wearing denim jeans fashion",
    },
    {
        "name": "Outerwear & Jackets",
        "description": "Blazers, jackets, and coats for transitional weather.",
        "query": "woman wearing blazer jacket fashion",
    },
    {
        "name": "Knitwear",
        "description": "Sweaters and cardigans in soft, wearable knits.",
        "query": "woman wearing knit sweater fashion",
    },
    {
        "name": "Activewear",
        "description": "Leggings, sports bras, and layers built to move in.",
        "query": "woman wearing activewear leggings fitness",
    },
    {
        "name": "Bags & Accessories",
        "description": "Handbags, belts, and the finishing pieces for any outfit.",
        "query": "woman fashion handbag accessory flatlay",
    },
]

# A handful of real products per category. Prices are in GHS to match the rest
# of the storefront (see PAYSTACK currency in app/paystack.py).
PRODUCTS = [
    {
        "category": "Dresses",
        "name": "Floral Wrap Midi Dress",
        "short_description": "A wrap silhouette in a soft floral print, cut for warm days.",
        "price": "165.00",
        "query": "floral wrap midi dress product photo",
        "is_featured": True,
        "variants": [("S", "Floral", 6), ("M", "Floral", 9), ("L", "Floral", 5)],
    },
    {
        "category": "Dresses",
        "name": "Satin Slip Dress",
        "short_description": "Bias-cut satin slip with adjustable straps.",
        "price": "139.00",
        "query": "satin slip dress product photo",
        "is_featured": False,
        "variants": [("S", "Champagne", 7), ("M", "Champagne", 8)],
    },
    {
        "category": "Tops & Blouses",
        "name": "Silk-Feel Tie-Neck Blouse",
        "short_description": "A relaxed blouse with a soft tie neckline.",
        "price": "98.00",
        "query": "tie neck blouse product photo",
        "is_featured": True,
        "variants": [("S", "Ivory", 10), ("M", "Ivory", 12), ("L", "Ivory", 6)],
    },
    {
        "category": "Tops & Blouses",
        "name": "Ribbed Knit Camisole",
        "short_description": "A fitted ribbed cami that layers under everything.",
        "price": "45.00",
        "query": "ribbed camisole top product photo",
        "is_featured": False,
        "variants": [("S", "Black", 15), ("M", "Black", 15), ("L", "Black", 8)],
    },
    {
        "category": "Skirts",
        "name": "Pleated Midi Skirt",
        "short_description": "A fluid pleated skirt that moves with every step.",
        "price": "112.00",
        "query": "pleated midi skirt product photo",
        "is_featured": True,
        "variants": [("S", "Sage", 6), ("M", "Sage", 8)],
    },
    {
        "category": "Jeans & Trousers",
        "name": "High-Rise Straight Jeans",
        "short_description": "A classic straight leg cut in rigid, non-stretch denim.",
        "price": "129.00",
        "query": "high rise straight jeans product photo",
        "is_featured": True,
        "variants": [("28", "Indigo", 8), ("30", "Indigo", 10), ("32", "Indigo", 6)],
    },
    {
        "category": "Jeans & Trousers",
        "name": "Tailored Wide-Leg Trousers",
        "short_description": "Wide-leg trousers with a crisp, tailored waistband.",
        "price": "134.00",
        "query": "wide leg tailored trousers product photo",
        "is_featured": False,
        "variants": [("S", "Charcoal", 7), ("M", "Charcoal", 9)],
    },
    {
        "category": "Outerwear & Jackets",
        "name": "Oversized Tailored Blazer",
        "short_description": "A boxy, oversized blazer that layers over anything.",
        "price": "189.00",
        "query": "oversized blazer jacket product photo",
        "is_featured": True,
        "variants": [("S", "Camel", 5), ("M", "Camel", 6)],
    },
    {
        "category": "Knitwear",
        "name": "Chunky Cable-Knit Cardigan",
        "short_description": "An oversized cardigan in a heavyweight cable knit.",
        "price": "108.00",
        "query": "chunky cable knit cardigan product photo",
        "is_featured": False,
        "variants": [("S", "Oatmeal", 8), ("M", "Oatmeal", 10)],
    },
    {
        "category": "Activewear",
        "name": "High-Waist Performance Leggings",
        "short_description": "Squat-proof leggings with a supportive high waistband.",
        "price": "79.00",
        "query": "high waist leggings product photo",
        "is_featured": True,
        "variants": [("S", "Black", 12), ("M", "Black", 14), ("L", "Black", 9)],
    },
    {
        "category": "Bags & Accessories",
        "name": "Structured Top-Handle Bag",
        "short_description": "A structured top-handle bag in grained leather.",
        "price": "159.00",
        "query": "structured top handle handbag product photo",
        "is_featured": True,
        "variants": [("One Size", "Tan", 6)],
    },
]


class Command(BaseCommand):
    help = (
        "Seeds a full women's clothing catalog (8 categories, ~12 products) with real "
        "photography pulled from Unsplash/Pexels. Requires UNSPLASH_ACCESS_KEY and/or "
        "PEXELS_API_KEY to be set -- see backend/app/stock_photos.py for how to get one. "
        "Safe to re-run: existing categories/products are matched by name and only "
        "missing images are (re)fetched unless --refresh-images is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Re-download and replace images even if one is already set.",
        )

    def handle(self, *args, **options):
        refresh = options["refresh_images"]
        categories_by_name = {}

        for cat_payload in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=cat_payload["name"],
                defaults={
                    "description": cat_payload["description"],
                    "slug": slugify(cat_payload["name"]),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))
            categories_by_name[category.name] = category

            if category.image and not refresh:
                continue

            photo = fetch_stock_photo(cat_payload["query"])
            if not photo:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped image for category '{category.name}' -- no stock photo "
                        "provider configured or reachable. Set UNSPLASH_ACCESS_KEY or "
                        "PEXELS_API_KEY in backend/.env and re-run with --refresh-images."
                    )
                )
                continue

            category.image.save(photo.filename, ContentFile(photo.content), save=False)
            category.image_credit = photo.credit
            category.save(update_fields=["image", "image_credit"])
            self.stdout.write(self.style.SUCCESS(f"Set image for category '{category.name}' ({photo.credit})"))

        for product_payload in PRODUCTS:
            category = categories_by_name.get(product_payload["category"])
            if category is None:
                self.stdout.write(self.style.ERROR(f"Unknown category for {product_payload['name']}, skipping."))
                continue

            product, created = Product.objects.get_or_create(
                name=product_payload["name"],
                defaults={
                    "category": category,
                    "short_description": product_payload["short_description"],
                    "description": product_payload["short_description"],
                    "base_price": Decimal(product_payload["price"]),
                    "is_featured": product_payload["is_featured"],
                    "slug": slugify(product_payload["name"]),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))

            for index, (size, color, stock) in enumerate(product_payload["variants"]):
                sku = f"{slugify(product.name).upper().replace('-', '_')}_{size}_{color}".upper()
                ProductVariant.objects.get_or_create(
                    product=product,
                    sku=sku,
                    defaults={
                        "size": size,
                        "color": color,
                        "stock_quantity": stock,
                        "price": Decimal(product_payload["price"]),
                        "is_default": index == 0,
                    },
                )

            existing_images = list(product.images.all())
            if existing_images and not refresh:
                continue

            photo = fetch_stock_photo(product_payload["query"])
            if not photo:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped image for product '{product.name}' -- no stock photo "
                        "provider configured or reachable."
                    )
                )
                continue

            if refresh:
                for existing_image in existing_images:
                    if existing_image.image:
                        existing_image.image.delete(save=False)
                    existing_image.delete()

            image = ProductImage(product=product, alt_text=product.name, credit=photo.credit, position=1)
            image.image.save(photo.filename, ContentFile(photo.content), save=False)
            image.save()
            self.stdout.write(self.style.SUCCESS(f"Set image for product '{product.name}' ({photo.credit})"))

        self.stdout.write(self.style.SUCCESS("Women's catalog seed complete."))
