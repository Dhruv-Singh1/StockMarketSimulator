# Generated by Django 3.2.12 on 2023-02-05 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0038_alter_newsitem_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='trading_active',
            field=models.BooleanField(default=True),
        ),
    ]