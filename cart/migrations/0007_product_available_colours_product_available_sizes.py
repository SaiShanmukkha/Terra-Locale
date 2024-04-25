# Generated by Django 5.0.3 on 2024-04-25 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0006_remove_product_available_colours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='available_colours',
            field=models.ManyToManyField(blank=True, null=True, to='cart.colourvariation'),
        ),
        migrations.AddField(
            model_name='product',
            name='available_sizes',
            field=models.ManyToManyField(blank=True, null=True, to='cart.sizevariation'),
        ),
    ]