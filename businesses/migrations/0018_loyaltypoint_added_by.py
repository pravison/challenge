# Generated by Django 5.1.4 on 2025-02-02 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0017_loyaltypointscategory_edited_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='loyaltypoint',
            name='added_by',
            field=models.CharField(default='juma', max_length=200),
            preserve_default=False,
        ),
    ]
