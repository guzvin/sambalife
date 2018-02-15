# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-02-15 17:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0016_accounting_is_sandbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='params',
            name='paypal_fee',
            field=models.DecimalField(decimal_places=2, default=4.4, max_digits=12, verbose_name='Desconto PayPal'),
        ),
    ]
