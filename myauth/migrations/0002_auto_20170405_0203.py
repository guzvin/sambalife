# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-05 02:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='phone',
            field=models.CharField(max_length=25, null=True, verbose_name='Telefone'),
        ),
    ]
