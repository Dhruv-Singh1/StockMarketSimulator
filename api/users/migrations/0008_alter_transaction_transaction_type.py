# Generated by Django 4.0.2 on 2022-03-05 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_transaction_transaction_type_alter_transaction_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('0', 'sell'), ('1', 'buy')], max_length=1),
        ),
    ]