# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-04 23:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0002_params_partner_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='params',
            name='elapse_one',
            field=models.SmallIntegerField(blank=True, default=30, help_text='Em dias.', null=True, verbose_name='Período Base'),
        ),
        migrations.AddField(
            model_name='params',
            name='elapse_three',
            field=models.SmallIntegerField(blank=True, default=15, help_text='Em dias. Após o segundo período.', null=True, verbose_name='Terceiro Período'),
        ),
        migrations.AddField(
            model_name='params',
            name='elapse_two',
            field=models.SmallIntegerField(blank=True, default=15, help_text='Em dias. Após o primeiro período.', null=True, verbose_name='Segundo Período'),
        ),
        migrations.AddField(
            model_name='params',
            name='redirect_factor_three',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.99, max_digits=12, null=True, verbose_name='Valor do Terceiro Período'),
        ),
        migrations.AddField(
            model_name='params',
            name='redirect_factor_two',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.49, max_digits=12, null=True, verbose_name='Valor do Segundo Período'),
        ),
        migrations.AlterField(
            model_name='params',
            name='redirect_factor',
            field=models.DecimalField(decimal_places=2, default=1.29, max_digits=12, verbose_name='Valor Base'),
        ),
    ]
