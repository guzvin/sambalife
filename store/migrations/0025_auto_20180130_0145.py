# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-30 01:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_auto_20180130_0137'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='collaborator',
            options={'verbose_name': 'Colaborador', 'verbose_name_plural': 'Colaboradores'},
        ),
        migrations.AlterField(
            model_name='lot',
            name='collaborator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.Collaborator', verbose_name='Colaborador'),
        ),
    ]
