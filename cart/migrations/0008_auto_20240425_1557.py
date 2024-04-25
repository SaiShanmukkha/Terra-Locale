# Generated by Django 3.1.1 on 2024-04-25 20:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0007_product_available_colours_product_available_sizes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='colour',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cart.colourvariation'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cart.sizevariation'),
        ),
    ]