# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-22 01:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0019_shipment_accounting'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='receive_date',
            field=models.DateTimeField(null=True, verbose_name='Data de Recebimento'),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='status',
            field=models.SmallIntegerField(choices=[(1, 'Preparando para Envio'), (2, 'Upload Etiqueta Caixa Autorizado'), (3, 'Pagamento Autorizado'), (4, 'Checagens Finais'), (5, 'Enviado')], verbose_name='Status'),
        ),
    ]
