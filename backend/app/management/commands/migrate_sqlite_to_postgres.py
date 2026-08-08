from pathlib import Path

from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.db import connections, transaction

from app.models import Cart, CartItem, Order, OrderItem, Payment
from products.models import Category, Product, ProductImage, ProductVariant, Review
from project import settings as project_settings
from users.models import User


class Command(BaseCommand):
    help = "Copy project data from the legacy SQLite database into Postgres"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-db-path",
            default=str(Path(project_settings.BASE_DIR) / "db.sqlite3"),
            help="Path to the SQLite database to copy from.",
        )
        parser.add_argument(
            "--source-alias",
            default="legacy_sqlite",
            help="Temporary database alias used for the SQLite source.",
        )
        parser.add_argument(
            "--target-alias",
            default="default",
            help="Database alias to copy into.",
        )
        parser.add_argument(
            "--flush-target",
            action="store_true",
            help="Flush the target database before copying data.",
        )

    def handle(self, *args, **options):
        source_path = Path(options["source_db_path"]).expanduser().resolve()
        source_alias = options["source_alias"]
        target_alias = options["target_alias"]
        flush_target = options["flush_target"]

        if not source_path.exists():
            raise CommandError(f"Source SQLite database not found: {source_path}")

        if source_alias == target_alias:
            raise CommandError("Source and target database aliases must be different.")

        connections.databases[source_alias] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(source_path),
        }

        models_to_copy = [
            User,
            Category,
            Product,
            ProductVariant,
            ProductImage,
            Review,
            Cart,
            Order,
            CartItem,
            OrderItem,
            Payment,
        ]

        if not flush_target:
            existing_rows = sum(model.objects.using(target_alias).count() for model in models_to_copy)
            if existing_rows:
                raise CommandError(
                    "Target database already contains project data. "
                    "Rerun with --flush-target to replace it."
                )

        if flush_target:
            call_command("flush", database=target_alias, interactive=False, verbosity=0)

        with transaction.atomic(using=target_alias):
            total_copied = 0
            for model in models_to_copy:
                copied = self.copy_model(model, source_alias, target_alias)
                total_copied += copied
                self.stdout.write(self.style.SUCCESS(f"Copied {copied} rows from {model._meta.label}"))

            self.reset_sequences(target_alias, models_to_copy)

        self.stdout.write(self.style.SUCCESS(f"Finished migrating {total_copied} rows into {target_alias}."))

    def copy_model(self, model, source_alias, target_alias):
        rows = list(model.objects.using(source_alias).values())
        if not rows:
            return 0

        instances = [model(**row) for row in rows]
        model.objects.using(target_alias).bulk_create(instances, batch_size=500)
        return len(instances)

    def reset_sequences(self, target_alias, models):
        connection = connections[target_alias]
        statements = connection.ops.sequence_reset_sql(no_style(), models)
        if not statements:
            return

        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
