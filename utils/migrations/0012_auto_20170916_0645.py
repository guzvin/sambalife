# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-09-16 06:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0011_params_contact_us_mail_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='params',
            name='contact_us_mail_to',
            field=models.CharField(blank=True, help_text='Separado por ponto e vírgula.', max_length=500, null=True, verbose_name='E-mail fale conosco'),
        ),
    ]
