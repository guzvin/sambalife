# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-29 13:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0012_auto_20170916_0645'),
    ]

    operations = [
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('type', models.SmallIntegerField(choices=[(1, 'Taxa fixa'), (2, 'Por serviços')], null=True, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo de cobrança',
                'verbose_name_plural': 'Tipo de cobrança',
            },
        ),
    ]