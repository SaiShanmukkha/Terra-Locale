import csv
from django.core.files import File
from django.core.management.base import BaseCommand
from core.models import Product

class Command(BaseCommand):
    help = 'Import products from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path')

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                product, created = Product.objects.get_or_create(
                    title=row['title'],
                    defaults={
                        'description': row['description'],
                        'slug': row['slug'],
                        'stock': int(row['stock']),
                        'active': row['active'] == 'True',
                        'price': float(row['price']),
                        'rating': float(row['rating']),
                    }
                )
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully added product: {product.title}'))
