# Generated by Django 4.0.2 on 2022-03-17 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_alter_transaction_portfolio_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsitem',
            name='related_stocks',
        ),
        migrations.AddField(
            model_name='newsitem',
            name='related_stocks',
            field=models.CharField(default='All', max_length=100),
        ),
    ]
