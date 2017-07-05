from django.db import models
from django.db.models.fields import BigAutoField
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
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
    payment_complete = models.BooleanField(_('Pagamento de reserva'), default=False)
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
    products_cost = models.DecimalField(_('Custo dos Produtos'), max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(_('Lucro'), max_digits=12, decimal_places=2, default=0)
    average_roi = models.DecimalField(_('ROI Médio'), max_digits=12, decimal_places=2, default=0)
    redirect_cost = models.DecimalField(_('Redirecionamento'), max_digits=12, decimal_places=2, default=0)
    lot_cost = models.DecimalField(_('Valor do Lote'), max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = _('Lote')
        verbose_name_plural = _('Lotes')

    def __str__(self):
        return self.name


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    identifier = models.CharField(_('UPC / Código Identificador'), max_length=50)
    url = models.URLField(_('URL do Produto'), max_length=500, null=True, blank=True)
    buy_price = models.DecimalField(_('Valor de Compra'), max_digits=12, decimal_places=2)
    sell_price = models.DecimalField(_('Valor de Venda'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    fba_fee = models.DecimalField(_('Tarifa FBA'), max_digits=12, decimal_places=2)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2,
                                     default=settings.DEFAULT_AMAZON_FEE)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2,
                                        default=settings.DEFAULT_AMAZON_SHIPPING_COST)
    redirect_factor = models.DecimalField(_('Redirecionamento'), max_digits=12, decimal_places=2,
                                          default=settings.DEFAULT_REDIRECT_FACTOR)
    product_cost = models.DecimalField(_('Custo do Produto'), max_digits=12, decimal_places=2, default=0)
    profit_per_unit = models.DecimalField(_('Lucro por Unidade'), max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(_('Lucro Total'), max_digits=12, decimal_places=2, default=0)
    roi = models.DecimalField(_('ROI'), max_digits=12, decimal_places=2, default=0)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
