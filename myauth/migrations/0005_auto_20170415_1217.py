# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-15 12:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0004_auto_20170412_0523'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='myuser',
            options={'permissions': (('view_admin', 'Pode visualizar Administração'),), 'verbose_name': 'Usuário', 'verbose_name_plural': 'Usuários'},
        ),
    ]
