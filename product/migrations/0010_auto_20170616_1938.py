# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-16 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_auto_20170523_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.SmallIntegerField(choices=[(1, 'Encaminhado VOI'), (2, 'Em Estoque VOI'), (99, 'Arquivado')], null=True, verbose_name='Status'),
        ),
    ]
