# Generated by Django 4.0.2 on 2022-03-05 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_portfolio_options_alter_stock_misc'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('0', 'sell'), ('1', 'buy')], default=None, max_length=1),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='price',
            field=models.IntegerField(),
        ),
    ]