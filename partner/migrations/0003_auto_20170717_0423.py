# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-17 04:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0002_auto_20170628_2355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='identity',
            field=models.CharField(max_length=4, unique=True, verbose_name='Sigla'),
        ),
    ]