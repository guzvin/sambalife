from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger('django')


class Service(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    price = models.DecimalField(_('Preço'), max_digits=12, decimal_places=2, help_text=_('Por unidade'))

    class Meta:
        verbose_name = _('Serviço')
        verbose_name_plural = _('Serviços')

    def __str__(self):
        return self.name


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    product = models.ForeignKey('shipment.Product', on_delete=models.CASCADE, related_name='service_products')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price = models.DecimalField(_('Preço'), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
