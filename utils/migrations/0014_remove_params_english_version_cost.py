# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-11-15 14:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0013_billing'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='params',
            name='english_version_cost',
        ),
    ]
