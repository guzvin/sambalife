# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-29 01:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0013_auto_20170628_2228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.Partner', verbose_name='Parceiro'),
        ),
    ]