from django.db import models
from django.db.models.fields import BigAutoField
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import ValidationError
from shipment.validators import validate_file_extension
from datetime import datetime
from product.models import Product as OriginalProduct
from utils.helper import Calculate
from pyparsing import ParseException
import logging

logger = logging.getLogger('django')


class Lot(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    description = models.TextField(_('Descrição'), null=True, blank=True)
    STATUS_CHOICES = (
        (1, _('Não vendido')),  # Available
        (2, _('Vendido')),  # Sold
    )
    status = models.SmallIntegerField(_('Situação'), choices=STATUS_CHOICES, default=1)
    create_date = models.DateField(_('Data de Cadastro'), auto_now_add=True)
    sell_date = models.DateField(_('Data da Venda'), null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'Grupos aos quais este lote pertence. Deixe em branco para não restringir o acesso à ele.'
        ),
        related_name="lot_set",
        related_query_name="lot",
    )
    # products_cost = ??
    # profit = soma de todos (total_profit) dos produtos no lote
    # average_roi = soma de todos (roi) divididos pelo número de produtos no lote
    # lot_cost = soma de todos (buy_price * quantity) de todos produtos do lote

    class Meta:
        verbose_name = _('Lote')
        verbose_name_plural = _('Lotes')


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    identifier = models.CharField(_('UPC / Código Identificador'), max_length=50)
    url = models.URLField(_('URL do Produto'), max_length=500, null=True, blank=True)
    buy_price = models.DecimalField(_('Valor de Compra'), max_digits=12, decimal_places=2)
    sell_price = models.DecimalField(_('Valor de Venda'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    fba_fee = models.DecimalField(_('Tarifa FBA'), max_digits=12, decimal_places=2)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2, default=0.99)
    shipping_cost = models.DecimalField(_('Custo de Envio'), max_digits=12, decimal_places=2, default=0.30)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)
    # product_cost = buy_price + amazon_fee + fba_fee + shipping_cost + redirect_factor(1.29)
    # profit_per_unit = sell_price - product_cost
    # total_profit = profit_per_unit * quantity
    # roi = profit_per_unit / product_cost

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
