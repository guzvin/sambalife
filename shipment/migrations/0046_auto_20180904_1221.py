# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-09-04 12:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0045_shipment_observations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shipment',
            options={'permissions': (('view_shipments', 'Pode visualizar Envios Amazon'), ('view_fbm_shipments', 'Pode visualizar Envios Merchant'), ('add_fbm_shipment', 'Pode adicionar Envios Merchant'), ('create_fba_shipment', 'Criar Envio FBA'), ('create_fba_shipment_admin', 'Criar Envio FBA Admin'), ('voi_prime', 'VOI Prime')), 'verbose_name': 'Envio', 'verbose_name_plural': 'Envios'},
        ),
    ]
