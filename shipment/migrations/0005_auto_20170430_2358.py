# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-30 23:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0004_auto_20170430_0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='cost',
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Valor Total'),
        ),
    ]
