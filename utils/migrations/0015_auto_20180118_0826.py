# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-18 08:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0014_remove_params_english_version_cost'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Billing',
        ),
        migrations.AlterField(
            model_name='params',
            name='fgr_cost',
            field=models.DecimalField(decimal_places=2, default=0.2, max_digits=12, verbose_name='Valor Repasse'),
        ),
    ]