# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-09-27 02:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0030_estimates_weekends'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shipment',
            name='send_date',
        ),
    ]
