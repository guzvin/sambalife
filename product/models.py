from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import ValidationError
from datetime import datetime
import logging

logger = logging.getLogger('django')


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    description = models.TextField(_('Descrição'), null=True, blank=True)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    send_date = models.DateField(_('Data de Envio'))
    STATUS_CHOICES = (
        (1, _('Enviado')),
        (2, _('Em Estoque')),
    )
    status = models.SmallIntegerField(_('Status'), choices=STATUS_CHOICES, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        permissions = (
            ('view_products', _('Pode visualizar Produtos')),
            ('change_product_status', _('Pode editar status do Produto')),
        )

    def clean(self):
        errors = {}
        if self.send_date and self.send_date > datetime.now().date():
            errors['send_date'] = ValidationError(_('Informe uma data menor ou igual a de hoje.'), code='invalid_date')
        if self.quantity:
            if self.quantity <= 0:
                errors['quantity'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_quantity')
        if bool(errors):
            raise ValidationError(errors)


class Tracking(models.Model):
    id = BigAutoField(primary_key=True)
    track_number = models.CharField(_('Rastreamento'), max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
