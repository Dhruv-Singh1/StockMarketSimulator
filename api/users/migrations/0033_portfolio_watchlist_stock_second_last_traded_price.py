# Generated by Django 4.0.3 on 2022-04-04 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_rename_inital_money_portfolio_initial_money'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='watchlist',
            field=models.ManyToManyField(blank=True, to='users.stock'),
        ),
        migrations.AddField(
            model_name='stock',
            name='second_last_traded_price',
            field=models.FloatField(default=0),
        ),
    ]
