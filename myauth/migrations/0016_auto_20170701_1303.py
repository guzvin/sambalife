# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-01 13:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0015_auto_20170629_0204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraddress',
            name='neighborhood',
        ),
        migrations.AddField(
            model_name='useraddress',
            name='country',
            field=models.CharField(max_length=2, null=True, verbose_name='País'),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='cell_phone',
            field=models.CharField(max_length=25, verbose_name='Telefone 1'),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='phone',
            field=models.CharField(max_length=25, null=True, verbose_name='Telefone 2'),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='state',
            field=models.CharField(max_length=100, verbose_name='Estado'),
        ),
    ]
