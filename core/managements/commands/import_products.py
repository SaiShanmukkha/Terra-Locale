import csv
from django.core.management.base import BaseCommand
from django.core.files import File
from io import BytesIO
from urllib.request import urlopen
from cart.models import Product, Category
from retrying import retry

class Command(BaseCommand):
    help = 'Loads a list of products from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path')

    @retry(wait_fixed=2000, stop_max_attempt_number=3)
    def fetch_image_content(self, image_url):
        return urlopen(image_url).read()

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                product, created = Product.objects.get_or_create(
                    title=row['title'],
                    defaults={
                        'description': row['description'],
                        'stock': int(row['stock']),
                        'price': float(row['price']),
                        'rating': float(row['rating']),
                        'slug': row['slug']
                    }
                )
                if created:
                    if row.get('primary_category'):
                        primary_category, _ = Category.objects.get_or_create(name=row['primary_category'])
                        product.primary_category = primary_category
                    
                    # Handling image if available
                    if row.get('image'):
                        # Assuming 'image' is the column name for image URLs
                        image_url = row['image']
                        image_name = image_url.split('/')[-1]  # Extracting image name from URL
                        try:
                            image_content = self.fetch_image_content(image_url)  # Reading image content from URL
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Error fetching image for product {product.title}: {e}'))
                            continue
                        image_file = BytesIO(image_content)  # Wrapping content in BytesIO
                        product.image.save(image_name, File(image_file), save=True)  # Saving image to product
                    
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully added product {product.title}'))
