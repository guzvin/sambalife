# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-23 02:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0033_lot_lifecycle_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='lot',
            name='lifecycle_open',
            field=models.BooleanField(default=False, verbose_name='Lifecycle aberto'),
        ),
    ]
