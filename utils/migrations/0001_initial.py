# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-11 09:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Params',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('redirect_factor', models.DecimalField(decimal_places=2, default=1.29, max_digits=12, verbose_name='Valor do Redirecionamento')),
                ('amazon_fee', models.DecimalField(decimal_places=2, default=0.99, max_digits=12, verbose_name='Tarifa Amazon')),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0.3, max_digits=12, verbose_name='Custo de Envio para Amazon')),
            ],
            options={
                'verbose_name_plural': 'Parametrizações',
                'verbose_name': 'Parametrizações',
            },
        ),
    ]