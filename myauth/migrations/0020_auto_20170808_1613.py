# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-08 16:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0019_auto_20170808_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='username_internal',
            field=models.CharField(max_length=156, null=True, unique=True, verbose_name='username'),
        ),
    ]