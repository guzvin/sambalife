# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-01-08 11:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_subscribe_execute_agreement_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscribe',
            name='agreement_id',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True, verbose_name='Agreement ID'),
        ),
    ]
