from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from app.image_generation import render_clothing_image


IMAGE_SPECS = [
    ("Linen Overshirt", "Lightweight layering piece for warm days."),
    ("Relaxed Denim Jacket", "Structured outerwear with a soft hand feel."),
    ("Ribbed Knit Polo", "Clean knitwear with a modern relaxed silhouette."),
    ("Tailored Trousers", "Sharp lines and an easy drape for everyday wear."),
    ("Summer Slip Dress", "Fluid shape with a soft, elegant finish."),
]


class Command(BaseCommand):
    help = "Generate studio-style clothing product images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-prefix",
            default="product_images",
            help="Storage folder where generated images will be written.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace files if they already exist in storage.",
        )

    def handle(self, *args, **options):
        output_prefix = options["output_prefix"].strip("/").rstrip("/")
        overwrite = options["overwrite"]

        for product_name, description in IMAGE_SPECS:
            image_file = render_clothing_image(product_name, description)
            storage_path = f"{output_prefix}/{slugify(product_name)}.jpg"

            if default_storage.exists(storage_path) and not overwrite:
                self.stdout.write(self.style.WARNING(f"Skipped existing image: {storage_path}"))
                continue

            saved_path = default_storage.save(storage_path, image_file)
            self.stdout.write(self.style.SUCCESS(f"Generated {saved_path}"))
