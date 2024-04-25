from django.utils.text import slugify


import random
import string
from rest_framework import serializers

from cart.models import Product

def generate_random_string(length=6):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'slug', 'stock', 'active', 'updated',
            'created', 'rating', 'image', 'price', 'primary_category'
        ]
        read_only_fields = ['slug']

    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['title']) + '-' + generate_random_string()
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
