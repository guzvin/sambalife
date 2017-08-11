# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-18 22:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0017_myuser_terms_conditions'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='language_code',
            field=models.CharField(choices=[('pt-br', 'Português'), ('en-us', 'Inglês')], default='pt-br', max_length=5, verbose_name='Idioma'),
        ),
    ]
