# Generated by Django 4.2.23 on 2025-07-10 20:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_status_order_timestamp_order_transactionid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='additonal_notes',
            new_name='additional_notes',
        ),
    ]
