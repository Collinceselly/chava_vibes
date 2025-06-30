from django.core.management.base import BaseCommand
from inventory.models import Product, Category
import csv

class Command(BaseCommand):
    help = 'Import products from CSV'

    def handle(self, *args, **options):
        with open('products.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                category, _ = Category.objects.get_or_create(name=row['category'])
                Product.objects.create(
                    name=row['name'],
                    price=row['price'],
                    description=row['description'],
                    category=category,
                    quantity=int(row['quantity']),
                    image=f"products/{row['image_filename']}"  # Links to media/products/
                )
        self.stdout.write(self.style.SUCCESS('Products imported successfully'))