# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-31 02:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0025_auto_20180130_0145'),
    ]

    operations = [
        migrations.AddField(
            model_name='collaborator',
            name='instructions',
            field=models.TextField(blank=True, null=True, verbose_name='Instruções'),
        ),
    ]
