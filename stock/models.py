from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from service.models import Service
import datetime

import logging

logger = logging.getLogger('django')


class Invoice(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    date = models.DateField(_('Data'))
    store = models.CharField(_('Loja'), max_length=150)
    origin = models.CharField(_('Origem'), max_length=150)

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return self.name


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    identifier = models.CharField(_('ASIN / UPC'), max_length=50, unique=True)
    upc = models.CharField(_('UPC'), max_length=50, null=True, blank=True)
    category = models.CharField(_('Categoria'), max_length=500, null=True, blank=True)
    url = models.URLField(_('URL do Produto'), max_length=500, null=True, blank=True)
    buy_price = models.DecimalField(_('Valor Cliente'), max_digits=12, decimal_places=2)
    sell_price = models.DecimalField(_('Valor Buy Box'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    fba_fee = models.DecimalField(_('FBA Fee'), max_digits=12, decimal_places=2)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2,
                                     default=0)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2,
                                        default=settings.DEFAULT_AMAZON_SHIPPING_COST)
    redirect_services = models.ManyToManyField(
        Service,
        verbose_name=_('services'),
        blank=False,
        help_text=_(
            'Serviços utilizados na preparação do envio.'
        ),
        related_name="stock_product_set",
        related_query_name="stock_product",
    )
    product_cost = models.DecimalField(_('Custo do Produto'), max_digits=12, decimal_places=2, default=0)
    profit_per_unit = models.DecimalField(_('Lucro por Unidade'), max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(_('Lucro Total'), max_digits=12, decimal_places=2, default=0)
    roi = models.DecimalField(_('ROI'), max_digits=12, decimal_places=2, default=0)
    rank = models.IntegerField(_('Rank'), default=0)
    voi_value = models.DecimalField(_('Custo VOI Services'), max_digits=12, decimal_places=2, default=0)
    CONDITION_CHOICES = (
        (1, _('New')),
        (2, _('Refurbished')),
        (3, _('Used Like New')),
        (4, _('Used Very Good')),
        (5, _('Used Good')),
        (6, _('Used Acceptable')),
    )
    condition = models.SmallIntegerField(_('Condição'), choices=CONDITION_CHOICES, null=True, blank=False)
    notes = models.TextField(_('Observação'), null=True, blank=True)
    invoices = models.ManyToManyField(
        Invoice,
        verbose_name=_('invoices'),
        blank=True,
        help_text=_(
            'Invoices aos quais este produto pertence.'  # 'The invoices this product belongs to.'
        ),
        related_name="stock_product_set",
        related_query_name="stock_product",
    )
    created_date = models.DateTimeField(_('Data de criação'), auto_now_add=True, null=True)
    changed_date = models.DateTimeField(_('Data de modificação'), default=datetime.datetime.now, null=True)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')

    def __str__(self):
        return self.name
