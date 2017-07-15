# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-14 14:26
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0004_auto_20170705_0201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='params',
            name='redirect_factor_three',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.99, max_digits=12, null=True, verbose_name='Valor Pós Segundo Período'),
        ),
        migrations.AlterField(
            model_name='params',
            name='redirect_factor_two',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.49, max_digits=12, null=True, verbose_name='Valor Pós Período Base'),
        ),
        migrations.AlterField(
            model_name='params',
            name='time_period_one',
            field=models.SmallIntegerField(blank=True, default=30, help_text='Em dias.', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Período Base'),
        ),
        migrations.AlterField(
            model_name='params',
            name='time_period_three',
            field=models.SmallIntegerField(blank=True, default=15, help_text='Em dias. Acumulativo com os períodos anteriores. Após este período o produto será considerado abandonado.', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Terceiro Período'),
        ),
        migrations.AlterField(
            model_name='params',
            name='time_period_two',
            field=models.SmallIntegerField(blank=True, default=15, help_text='Em dias. Acumulativo com o período base.', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Segundo Período'),
        ),
    ]
