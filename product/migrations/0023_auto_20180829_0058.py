# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-08-29 00:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0022_auto_20180812_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=150, verbose_name='Nome do Produto'),
        ),
    ]
