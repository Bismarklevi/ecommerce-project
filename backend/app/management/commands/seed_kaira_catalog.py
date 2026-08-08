"""Seeds the exact catalog the new (Next.js 16, 'kaira') frontend was designed
around: 5 categories, 14 products, real product photography (not stock
photos, not generated illustrations) bundled in
app/seed_assets/kaira_products/.

This is the catalog of record for that frontend -- product names, slugs,
descriptions, and prices here match frontend/src/lib/mock-data.ts exactly, so
swapping the frontend from mock data to real API calls produces the same
storefront content, just served from the database instead of a TypeScript
file.
"""
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product, ProductImage, ProductVariant

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "seed_assets" / "kaira_products"

CATEGORIES = [
    ("Dresses", "dresses"),
    ("Knitwear", "knitwear"),
    ("Tailoring", "tailoring"),
    ("Denim", "denim"),
    ("Accessories", "accessories"),
]

# (slug, name, category_slug, description, price, sizes, is_featured, images)
# images: list of (filename in ASSETS_DIR, alt text)
PRODUCTS = [
    (
        "floral-wrap-midi-dress", "Floral Wrap Midi Dress", "dresses",
        "A rust-red botanical print cut on the bias, finished with flutter sleeves and a "
        "self-tie waist that wraps to your shape. Fully lined.",
        "128.00", ["XS", "S", "M", "L", "XL"], True,
        [
            ("floral-wrap-midi-dress.jpg", "Floral Wrap Midi Dress, front"),
            ("floral-wrap-midi-dress-alt.jpg", "Floral Wrap Midi Dress, detail"),
        ],
    ),
    (
        "chunky-cable-knit-cardigan", "Chunky Cable-Knit Cardigan", "knitwear",
        "Hand-finished cable stitching in a heavyweight wool blend. Drop shoulders, horn "
        "buttons, made to be lived in through the coldest months.",
        "168.00", ["XS", "S", "M", "L"], False,
        [("chunky-cable-knit-cardigan.jpg", "Chunky Cable-Knit Cardigan")],
    ),
    (
        "high-rise-straight-jeans", "High-Rise Straight Jeans", "denim",
        "Rigid, non-stretch denim in a clean straight leg. Sits at the natural waist. "
        "Break in over time, wear out with intention.",
        "98.00", ["24", "25", "26", "27", "28", "29", "30"], False,
        [("high-rise-straight-jeans.jpg", "High-Rise Straight Jeans")],
    ),
    (
        "high-waist-performance-leggings", "High-Waist Performance Leggings", "accessories",
        "Four-way stretch with a wide, non-roll waistband. Squat-proof opacity, "
        "flat-locked seams. Built for movement.",
        "64.00", ["XS", "S", "M", "L", "XL"], True,
        [("high-waist-performance-leggings.jpg", "High-Waist Performance Leggings")],
    ),
    (
        "oversized-tailored-blazer", "Oversized Tailored Blazer", "tailoring",
        "Structured shoulders, a single button closure, and a fit designed to be worn "
        "open. Sharp enough for the office, loose enough for everything else.",
        "215.00", ["XS", "S", "M", "L"], False,
        [("oversized-tailored-blazer.jpg", "Oversized Tailored Blazer")],
    ),
    (
        "pleated-midi-skirt", "Pleated Midi Skirt", "tailoring",
        "Knife pleats that hold their line, finished at mid-calf with a concealed side "
        "zip. Moves with every step.",
        "89.00", ["XS", "S", "M", "L"], False,
        [("pleated-midi-skirt.jpg", "Pleated Midi Skirt")],
    ),
    (
        "ribbed-knit-camisole", "Ribbed Knit Camisole", "knitwear",
        "A fine-rib layering piece with adjustable straps and a scoop neck. Wear it "
        "alone or under everything else.",
        "42.00", ["XS", "S", "M", "L", "XL"], False,
        [("ribbed-knit-camisole.jpg", "Ribbed Knit Camisole")],
    ),
    (
        "satin-slip-dress", "Satin Slip Dress", "dresses",
        "Bias-cut satin that skims rather than clings. Adjustable straps, a low back, "
        "and a hem that hits just below the knee.",
        "142.00", ["XS", "S", "M", "L"], True,
        [("satin-slip-dress.jpg", "Satin Slip Dress")],
    ),
    (
        "silk-feel-tie-neck-blouse", "Silk-Feel Tie-Neck Blouse", "tailoring",
        "A fluid, lightweight blouse with a self-tie neck and covered button placket. "
        "Effortless with tailoring or denim.",
        "76.00", ["XS", "S", "M", "L"], False,
        [("silk-feel-tie-neck-blouse.jpg", "Silk-Feel Tie-Neck Blouse")],
    ),
    (
        "structured-top-handle-bag", "Structured Top-Handle Bag", "accessories",
        "A boxy silhouette in grained leather with a detachable strap and a top handle "
        "sized to sit at the crook of your arm.",
        "185.00", ["One Size"], True,
        [("structured-top-handle-bag.jpg", "Structured Top-Handle Bag")],
    ),
    (
        "wide-leg-tailored-trousers", "Wide-Leg Tailored Trousers", "tailoring",
        "High-waisted with a sharp center crease and a fluid drape through the leg. Cut "
        "long to sit just above the floor.",
        "112.00", ["XS", "S", "M", "L", "XL"], False,
        [("wide-leg-tailored-trousers.jpg", "Wide-Leg Tailored Trousers")],
    ),
    (
        "cream-tiered-dress", "Cream Tiered Dress", "dresses",
        "Soft tiers from waist to hem for easy movement, with a square neckline and "
        "short sleeves. An easy warm-weather staple.",
        "94.00", ["XS", "S", "M", "L"], True,
        [("cream-tiered-dress.jpg", "Cream Tiered Dress")],
    ),
    (
        "tailored-office-dress", "Tailored Office Dress", "dresses",
        "A structured sheath with a welt-pocket detail and a fitted waist seam. One "
        "piece, fully resolved.",
        "134.00", ["XS", "S", "M", "L", "XL"], False,
        [("tailored-office-dress.jpg", "Tailored Office Dress")],
    ),
    (
        "silk-cowl-dress", "Silk Cowl Dress", "dresses",
        "A draped cowl neckline falls into a column silhouette. Weighted hem, minimal "
        "seaming, maximum drape.",
        "158.00", ["XS", "S", "M", "L"], False,
        [("silk-cowl-dress.jpg", "Silk Cowl Dress")],
    ),
]


class Command(BaseCommand):
    help = "Seed the real Kaira catalog (categories, products, variants, real photography)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite-images",
            action="store_true",
            help="Replace product images even if the product already has one.",
        )

    def handle(self, *args, **options):
        overwrite_images = options["overwrite_images"]

        categories_by_slug = {}
        for name, slug in CATEGORIES:
            category, created = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            categories_by_slug[slug] = category
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Found'} category: {name}"))

        for (
            slug, name, category_slug, description, price, sizes, is_featured, images,
        ) in PRODUCTS:
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "category": categories_by_slug[category_slug],
                    "short_description": description[:255],
                    "description": description,
                    "base_price": Decimal(price),
                    "is_featured": is_featured,
                },
            )
            if not created:
                # Keep price/description/featured flag in sync on re-runs,
                # without touching variants/images that might have real
                # stock numbers by now.
                product.name = name
                product.category = categories_by_slug[category_slug]
                product.short_description = description[:255]
                product.description = description
                product.base_price = Decimal(price)
                product.is_featured = is_featured
                product.save()
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} product: {name}"))

            for index, size in enumerate(sizes):
                sku = f"{slug}-{size}".upper().replace(" ", "-")
                ProductVariant.objects.get_or_create(
                    product=product,
                    sku=sku,
                    defaults={
                        "size": size,
                        "color": "Default",
                        "stock_quantity": 20,
                        "price": Decimal(price),
                        "is_default": index == 0,
                    },
                )

            existing_images = list(product.images.all())
            if existing_images and not overwrite_images:
                continue

            if overwrite_images:
                for existing_image in existing_images:
                    if existing_image.image:
                        existing_image.image.delete(save=False)
                    existing_image.delete()

            for position, (filename, alt_text) in enumerate(images, start=1):
                source_path = ASSETS_DIR / filename
                if not source_path.exists():
                    self.stdout.write(self.style.ERROR(f"  Missing seed asset: {source_path}"))
                    continue
                image = ProductImage(product=product, alt_text=alt_text, position=position)
                image.image.save(filename, ContentFile(source_path.read_bytes()), save=False)
                image.save()
            self.stdout.write(self.style.SUCCESS(f"  -> set {len(images)} image(s) for '{name}'"))

        # A category tile with no image is a blank box on the homepage --
        # reuse each category's first product photo as its representative
        # image rather than requiring separate category-hero assets.
        for category in categories_by_slug.values():
            if category.image:
                continue
            representative = category.products.prefetch_related("images").first()
            if not representative:
                continue
            representative_image = representative.images.first()
            if not representative_image or not representative_image.image:
                continue
            category.image.save(
                representative_image.image.name.rsplit("/", 1)[-1],
                ContentFile(representative_image.image.read()),
                save=True,
            )
            self.stdout.write(self.style.SUCCESS(f"  -> set category image for '{category.name}'"))

        self.stdout.write(self.style.SUCCESS("Kaira catalog seeded."))
