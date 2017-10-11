# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-10-10 02:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0021_auto_20170912_2107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='myuser',
            name='username_internal',
        ),
        migrations.AlterField(
            model_name='myuser',
            name='email',
            field=models.CharField(max_length=150, unique=True, verbose_name='E-mail'),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='language_code',
            field=models.CharField(choices=[('pt', 'Português'), ('en', 'Inglês')], default='pt', max_length=5, verbose_name='Idioma'),
        ),
    ]