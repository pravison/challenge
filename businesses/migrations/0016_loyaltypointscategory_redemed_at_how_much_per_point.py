# Generated by Django 5.1.4 on 2025-02-02 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0015_remove_loyaltypoint_average_purchase_per_point_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loyaltypointscategory',
            name='redemed_at_how_much_per_point',
            field=models.FloatField(default=0.5),
        ),
    ]
