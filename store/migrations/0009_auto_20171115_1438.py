# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-11-15 14:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_auto_20170717_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lot',
            name='sell_date',
            field=models.DateTimeField(null=True, verbose_name='Data da Venda'),
        ),
    ]
