# Generated by Django 4.0.2 on 2022-02-18 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_stock_portfolio_value_transaction_newsitem_holding'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsitem',
            name='media_links',
            field=models.TextField(blank=True),
        ),
    ]
