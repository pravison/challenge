# Generated by Django 5.1.4 on 2025-01-14 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0001_initial'),
        ('customers', '0002_customer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='business',
            name='customers',
            field=models.ManyToManyField(blank=True, to='customers.customer'),
        ),
    ]
