# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-14 22:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0010_auto_20170514_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='shipment',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Código UPS'),
        ),
    ]