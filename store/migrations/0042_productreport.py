# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-11-14 16:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0041_product_upc'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReport',
            fields=[
            ],
            options={
                'verbose_name': 'Relatório de Produtos dos Lotes',
                'proxy': True,
                'verbose_name_plural': 'Relatório de Produtos dos Lotes',
            },
            bases=('store.product',),
        ),
    ]
