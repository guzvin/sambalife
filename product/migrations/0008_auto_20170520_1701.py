# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-20 17:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_product_quantity_partial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.SmallIntegerField(choices=[(1, 'Enviado'), (2, 'Em Estoque'), (99, 'Arquivado')], null=True, verbose_name='Status'),
        ),
    ]
