# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-16 02:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0009_auto_20170416_2354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='doc_number',
            field=models.CharField(max_length=25, null=True, verbose_name='CPF'),
        ),
    ]