# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-23 13:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import shipment.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0005_auto_20170422_1404'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('weight', models.FloatField(verbose_name='Peso')),
                ('height', models.FloatField(verbose_name='H')),
                ('width', models.FloatField(verbose_name='W')),
                ('length', models.FloatField(verbose_name='L')),
                ('weight_units', models.SmallIntegerField(choices=[(1, 'Pound'), (2, 'Ounce'), (3, 'Quilograma'), (4, 'Grama')], default=1, verbose_name='Unidade de medida de peso')),
                ('length_units', models.SmallIntegerField(choices=[(1, 'Centímetro'), (2, 'Milímetro'), (3, 'Inch')], default=1, verbose_name='Unidade de medida de tamanho')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('quantity', models.FloatField(verbose_name='Quantidade')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('total_products', models.FloatField(verbose_name='Total de Produtos')),
                ('cost', models.FloatField(verbose_name='Valor Total')),
                ('send_date', models.DateField(verbose_name='Data de Envio')),
                ('status', models.SmallIntegerField(choices=[(1, 'Preparando para Envio'), (2, 'Pagamento Autorizado'), (3, 'Upload PDF 2 autorizado'), (4, 'Checagens Finais'), (5, 'Enviado')], verbose_name='Status')),
                ('pdf_1', models.FileField(upload_to=shipment.models.user_directory_path, verbose_name='PDF 1')),
                ('pdf_2', models.FileField(null=True, upload_to=shipment.models.user_directory_path, verbose_name='PDF 2')),
                ('shipment', models.FileField(null=True, upload_to=shipment.models.user_directory_path, verbose_name='Comprovante de Envio')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Envio',
                'verbose_name_plural': 'Envios',
                'permissions': (('view_shipments', 'Pode visualizar Envios'),),
            },
        ),
        migrations.AddField(
            model_name='product',
            name='shipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shipment.Shipment'),
        ),
        migrations.AddField(
            model_name='package',
            name='shipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shipment.Shipment'),
        ),
    ]
