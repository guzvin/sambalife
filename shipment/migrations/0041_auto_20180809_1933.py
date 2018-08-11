# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-08-09 19:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0040_auto_20180809_1659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Criar Envio'), (1, 'Preparando para Envio'), (2, 'Upload Etiqueta Caixa Autorizado'), (3, 'Pagamento Autorizado'), (4, 'Checagens Finais'), (5, 'Enviado')], verbose_name='Status'),
        ),
    ]
