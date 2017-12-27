# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-12-27 03:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='lot',
            name='rank',
            field=models.IntegerField(default=0, verbose_name='Rank'),
        ),
        migrations.AlterField(
            model_name='config',
            name='default_group',
            field=models.OneToOneField(blank=True, help_text='Grupo ao qual os lotes e os usuários assinantes serão associados por padrão.', on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='Grupo padrão'),
        ),
    ]
