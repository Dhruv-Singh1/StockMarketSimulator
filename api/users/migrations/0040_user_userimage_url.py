# Generated by Django 3.2.12 on 2023-03-20 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0039_stock_trading_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='userimage_url',
            field=models.URLField(default='default.jpg'),
        ),
    ]