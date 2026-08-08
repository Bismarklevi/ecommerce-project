"""Seeds real category tile photography using static, pre-verified image URLs
-- no Unsplash/Pexels API key, no download, no network dependency at all.
Every URL below was pulled from a live Unsplash photo page and confirmed to
be under the free Unsplash License (not Unsplash+/premium).

Use this when you need working photos *right now* (e.g. before a demo) and
don't have time to set up `UNSPLASH_ACCESS_KEY`/`PEXELS_API_KEY` for the
fuller `seed_womens_catalog` command. You can swap these for downloaded,
Cloudflare-R2-hosted images later without changing any frontend code --
`Category.image` (an uploaded file) always wins over `Category.image_url`
(this static fallback) once you do.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product, ProductImage

# Each entry: category/product name -> (image URL, credit).
# All images: Unsplash License (free to use, attribution appreciated).
STATIC_IMAGES = {
    "Dresses": (
        "https://images.unsplash.com/photo-1753192105348-3b263840b73b?auto=format&fit=crop&w=1200&q=80",
        "Photo by Muhammad Nadir on Unsplash",
    ),
    "Tops & Blouses": (
        "https://images.unsplash.com/photo-1564595076323-71cc27edacf8?auto=format&fit=crop&w=1200&q=80",
        "Photo by WoodWatch on Unsplash",
    ),
    "Skirts": (
        "https://images.unsplash.com/photo-1552874869-5c39ec9288dc?auto=format&fit=crop&w=1200&q=80",
        "Photo by Khaled Ghareeb on Unsplash",
    ),
    "Jeans & Trousers": (
        "https://images.unsplash.com/photo-1517805686688-47dd930554b2?auto=format&fit=crop&w=1200&q=80",
        "Photo by Jon Ly on Unsplash",
    ),
    "Outerwear & Jackets": (
        "https://images.unsplash.com/photo-1685703206267-314ce44ca3c8?auto=format&fit=crop&w=1200&q=80",
        "Photo by Centre for Ageing Better on Unsplash",
    ),
    "Knitwear": (
        "https://images.unsplash.com/photo-1573587302894-7d0475939841?auto=format&fit=crop&w=1200&q=80",
        "Photo by Brian Asare on Unsplash",
    ),
    "Activewear": (
        "https://images.unsplash.com/photo-1584863495140-a320b13a11a8?auto=format&fit=crop&w=1200&q=80",
        "Photo by Subtle Cinematics on Unsplash",
    ),
    "Bags & Accessories": (
        "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?auto=format&fit=crop&w=1200&q=80",
        "Photo by Irene Kredenets on Unsplash",
    ),
}


class Command(BaseCommand):
    help = (
        "Sets a static, pre-verified photo URL on each category (and its products, if any "
        "exist yet) -- no API key, no download, works instantly. Run seed_womens_catalog "
        "first if you want the categories/products to exist; this command only sets images."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace images even on categories/products that already have one.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]

        for name, (url, credit) in STATIC_IMAGES.items():
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))

            if category.image_url and not overwrite:
                self.stdout.write(f"Skipped '{category.name}' (already has an image_url).")
            else:
                category.image_url = url
                category.image_credit = credit
                category.save(update_fields=["image_url", "image_credit"])
                self.stdout.write(self.style.SUCCESS(f"Set static image for category '{category.name}'"))

            for product in category.products.all():
                existing = product.images.first()
                if existing and not overwrite:
                    continue
                if existing:
                    existing.image_url = url
                    existing.credit = credit
                    existing.save(update_fields=["image_url", "credit"])
                else:
                    ProductImage.objects.create(
                        product=product,
                        image_url=url,
                        alt_text=product.name,
                        credit=credit,
                        position=1,
                    )
                self.stdout.write(self.style.SUCCESS(f"  -> also set image for product '{product.name}'"))

        self.stdout.write(self.style.SUCCESS("Static catalog images set."))
