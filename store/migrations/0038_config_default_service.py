# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-09-05 19:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0006_auto_20180119_1400'),
        ('store', '0037_auto_20180721_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='default_service',
            field=models.OneToOneField(blank=True, help_text='Serviço ao qual os produtos serão associados por padrão.', null=True, on_delete=django.db.models.deletion.CASCADE, to='service.Service', verbose_name='Serviço padrão'),
        ),
    ]