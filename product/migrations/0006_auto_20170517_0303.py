# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-17 03:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_auto_20170422_1404'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='quantity',
            field=models.PositiveIntegerField(verbose_name='Quantidade'),
        ),
    ]
