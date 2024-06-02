# Generated by Django 4.0.3 on 2022-03-27 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_rename_money_portfolio_actual_money_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClosedTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('price', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('transaction_type', models.CharField(max_length=1)),
                ('stop_limit', models.IntegerField(blank=True, null=True)),
                ('portfolio_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.portfolio')),
            ],
            options={
                'ordering': ['-status', '-stock_id', '-price'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('price', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('transaction_type', models.CharField(max_length=1)),
                ('stop_limit', models.IntegerField(blank=True, null=True)),
                ('portfolio_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.portfolio')),
            ],
            options={
                'ordering': ['-status', '-stock_id', '-price'],
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='closed_transaction',
            name='portfolio_id',
        ),
        migrations.RemoveField(
            model_name='closed_transaction',
            name='stock_id',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='current_market_price',
        ),
        migrations.AddField(
            model_name='stock',
            name='deviation_percentage',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='fame_counter',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='fourth_last_traded_price',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='last_traded_price',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='second_last_traded_price',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='stock',
            name='third_last_traded_price',
            field=models.FloatField(default=0),
        ),
        migrations.DeleteModel(
            name='Open_Transaction',
        ),
        migrations.AddField(
            model_name='opentransaction',
            name='stock_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.stock'),
        ),
        migrations.AddField(
            model_name='closedtransaction',
            name='stock_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.stock'),
        ),
        migrations.AlterField(
            model_name='holding',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.closedtransaction'),
        ),
        migrations.DeleteModel(
            name='Closed_Transaction',
        ),
    ]
