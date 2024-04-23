import csv
from django.core.management.base import BaseCommand
from cart.models import Product, Category

class Command(BaseCommand):
    help = 'Loads a list of products from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path')

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # Use the csvfile variable, not a string path
            for row in reader:
                product, created = Product.objects.get_or_create(
                    title=row['title'],
                    defaults={
                        'description': row['description'],
                        'stock': int(row['stock']),
                        'price': float(row['price']),
                        'rating': float(row['rating']),
                        'slug': row['slug'],
                        # Uncomment the following line if images are handled
                        # 'image': File(open(row['image_path'], 'rb')) if row.get('image_path') else None
                    }
                )
                if created:
                    # Categories are handled as an example of many-to-many relationships
                    if row.get('primary_category'):
                        primary_category, _ = Category.objects.get_or_create(name=row['primary_category'])
                        product.primary_category = primary_category
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully added product {product.title}'))

                # Similar logic would apply for other many-to-many relationships (sizes, colours, etc.)
