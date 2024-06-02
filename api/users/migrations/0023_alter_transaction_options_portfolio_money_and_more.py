# Generated by Django 4.0.2 on 2022-03-17 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_merge_20220317_2113'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-status', '-stock_id', '-price']},
        ),
        migrations.AddField(
            model_name='portfolio',
            name='money',
            field=models.FloatField(default=5000),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(max_length=1),
        ),
    ]