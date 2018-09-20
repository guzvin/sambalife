# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-09-14 15:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0038_config_default_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='lot',
            name='destination',
            field=models.SmallIntegerField(choices=[(1, 'Amazon'), (2, 'Ebay')], default=1, verbose_name='Destino'),
        ),
    ]