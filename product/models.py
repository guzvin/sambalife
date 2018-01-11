from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import ValidationError
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger('django')


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    asin = models.CharField(_('ASIN'), max_length=50, null=True, blank=True)
    store = models.CharField(_('Loja'), max_length=200, null=True, blank=True)
    description = models.TextField(_('Descrição'), null=True, blank=True)
    quantity_original = models.PositiveIntegerField(_('Quantidade Original Cadastrada'), null=True)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    quantity_partial = models.PositiveIntegerField(_('Quantidade Parcial'), null=True, blank=True)
    send_date = models.DateField(_('Data da Compra'))
    STATUS_CHOICES = (
        (1, _('Encaminhado VOI')),
        (2, _('Em Estoque VOI')),
        (99, _('Arquivado')),
        (100, _('Abandonado')),
    )
    status = models.SmallIntegerField(_('Status'), choices=STATUS_CHOICES, null=True, blank=True)
    CONDITION_CHOICES = (
        (1, _('New')),
        (2, _('Refurbished')),
        (3, _('Used Like New')),
        (4, _('Used Very Good')),
        (5, _('Used Good')),
        (6, _('Used Acceptable')),
    )
    condition = models.SmallIntegerField(_('Condição'), choices=CONDITION_CHOICES, null=True)
    actual_condition = models.SmallIntegerField(_('Condição no Recebimento'), choices=CONDITION_CHOICES, null=True,
                                                blank=True)
    condition_comments = models.CharField(_('Comentários da Condição'), max_length=200, null=True, blank=True)
    best_before = models.DateTimeField(_('Data de Validade'), null=True, blank=True)
    create_date = models.DateTimeField(_('Data de Cadastro'), auto_now_add=True, null=True)
    receive_date = models.DateTimeField(_('Data de Recebimento'), null=True, blank=True)
    edd_date = models.DateField(_('Previsão de Entrega'), null=True, blank=True)
    pick_ticket = models.CharField(_('Localização na Warehouse'), max_length=200, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    lot_product = models.ForeignKey('store.Product', null=True)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        permissions = (
            ('view_products', _('Pode visualizar Produtos')),
            ('change_product_status', _('Pode editar status do Produto')),
        )

    def clean(self):
        errors = {}
        logger.debug('@@@@@@@@@@@@ PRODUCT CLEAN SEND DATE @@@@@@@@@@@@@@')
        logger.debug(self.best_before)
        logger.debug(self.create_date)
        logger.debug(self.send_date)
        logger.debug(datetime.now())
        logger.debug(timezone.now())
        if self.send_date and self.send_date > datetime.now().date():
            errors['send_date'] = ValidationError(_('Informe uma data menor ou igual a de hoje.'), code='invalid_date')
        if (self.send_date and self.edd_date and self.edd_date <= self.send_date) \
                or (self.send_date is None and self.edd_date):
            errors['edd_date'] = ValidationError(_('Informe uma data maior que a Data da compra.'),
                                                 code='invalid_edd_date')
        if self.quantity:
            if self.quantity < 0:
                errors['quantity'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_quantity')
            if self.quantity_partial:
                if self.quantity_partial < 0:
                    errors['quantity_partial'] = ValidationError(_('Informe um número maior que zero.'),
                                                                 code='invalid_quantity_partial')
                elif self.quantity_partial > self.quantity:
                    self.quantity = self.quantity_partial
        if bool(errors):
            raise ValidationError(errors)


class Tracking(models.Model):
    id = BigAutoField(primary_key=True)
    track_number = models.CharField(_('Rastreamento'), max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
