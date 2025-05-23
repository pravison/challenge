# Generated by Django 5.1.4 on 2025-02-02 09:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0018_loyaltypoint_added_by'),
        ('customers', '0004_customer_total_loyalty_points'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_loyal_points', models.IntegerField(default=0)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='businesses.business')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customer')),
            ],
        ),
    ]
