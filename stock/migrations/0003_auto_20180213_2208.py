# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-13 22:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_product_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150, verbose_name='Nome')),
                ('date', models.DateTimeField(verbose_name='Data')),
                ('store', models.CharField(max_length=150, verbose_name='Loja')),
                ('origin', models.CharField(max_length=150, verbose_name='Origem')),
            ],
            options={
                'verbose_name': 'Invoice',
                'verbose_name_plural': 'Invoices',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='invoices',
            field=models.ManyToManyField(blank=True, help_text='The invoices this product belongs to.', related_name='stock_product_set', related_query_name='stock_product', to='stock.Invoice', verbose_name='invoices'),
        ),
    ]