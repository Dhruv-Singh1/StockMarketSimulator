# Generated by Django 4.0.2 on 2022-03-17 08:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_alter_transaction_portfolio_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='portfolio_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_id', to='users.portfolio'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='stock_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_id', to='users.stock'),
        ),
    ]
