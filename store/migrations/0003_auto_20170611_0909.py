# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-11 09:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_auto_20170609_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='redirect_factor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Redirecionamento'),
        ),
    ]
