# Generated by Django 4.0.3 on 2022-04-06 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0036_alter_portfolio_initial_money_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='closedtransaction',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='opentransaction',
            name='price',
            field=models.FloatField(),
        ),
    ]
