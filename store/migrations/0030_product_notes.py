# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-09 01:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0029_product_product_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Observação'),
        ),
    ]
