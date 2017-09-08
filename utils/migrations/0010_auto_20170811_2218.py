# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-11 22:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0009_params_fgr_cost'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='params',
            name='partner_cost',
        ),
        migrations.AddField(
            model_name='params',
            name='english_version_cost',
            field=models.DecimalField(decimal_places=2, default=0.2, max_digits=12, verbose_name='Valor Extra da Versão em Inglês'),
        ),
    ]