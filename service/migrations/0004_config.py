# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-28 09:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0003_auto_20171022_1902'),
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('minimum_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Preço mínimo total')),
            ],
        ),
    ]
