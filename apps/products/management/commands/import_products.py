import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.products.models import Product


class Command(BaseCommand):
    help = "Import products from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to the products CSV file.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing products before importing.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        required_columns = {
            "id",
            "product_name",
            "product_description",
            "category",
            "tags",
        }

        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise CommandError("CSV file has no header row.")

                missing_columns = required_columns - set(reader.fieldnames)

                if missing_columns:
                    raise CommandError(
                        f"CSV is missing required columns: {', '.join(sorted(missing_columns))}"
                    )

                products = []

                for row_number, row in enumerate(reader, start=2):
                    try:
                        product_id = int(row["id"])
                        product_name = row["product_name"].strip()
                        product_description = row["product_description"].strip()
                        category = row["category"].strip()

                        tags = [
                            tag.strip().lower()
                            for tag in row["tags"].split(",")
                            if tag.strip()
                        ]

                        if not product_name or not category:
                            raise ValueError(
                                "product_name and category cannot be empty."
                            )

                        products.append(
                            Product(
                                id=product_id,
                                product_name=product_name,
                                product_description=product_description,
                                category=category,
                                tags=tags,
                            )
                        )
                    except (ValueError, AttributeError) as error:
                        raise CommandError(
                            f"Invalid data at CSV row {row_number}: {error}"
                        ) from error

        except UnicodeDecodeError as error:
            raise CommandError(
                "Unable to read CSV. Save it as UTF-8 and try again."
            ) from error

        with transaction.atomic():
            if options["clear"]:
                deleted_count, _ = Product.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Deleted {deleted_count} existing product record(s)."
                    )
                )

            Product.objects.bulk_create(
                products,
                batch_size=500,
                ignore_conflicts=True,
            )

        total_products = Product.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. CSV rows processed: {len(products)}. "
                f"Total products in database: {total_products}."
            )
        )