# Generated by Django 4.0.3 on 2022-04-01 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_remove_stock_fourth_last_traded_price_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='closedtransaction',
            options={},
        ),
        migrations.AlterModelOptions(
            name='opentransaction',
            options={},
        ),
        migrations.RemoveField(
            model_name='closedtransaction',
            name='status',
        ),
        migrations.RemoveField(
            model_name='closedtransaction',
            name='stop_limit',
        ),
        migrations.RemoveField(
            model_name='opentransaction',
            name='status',
        ),
        migrations.RemoveField(
            model_name='opentransaction',
            name='stop_limit',
        ),
        migrations.RemoveField(
            model_name='portfolio',
            name='actual_money',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='available_quantity',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='deviation_percentage',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='fame_counter',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='slug',
        ),
        migrations.AddField(
            model_name='portfolio',
            name='inital_money',
            field=models.FloatField(default=5000),
        ),
        migrations.AlterField(
            model_name='stock',
            name='ask_price',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='stock',
            name='bid_price',
            field=models.FloatField(default=0),
        ),
    ]
