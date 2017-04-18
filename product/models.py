from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    description = models.TextField(_('Descrição'), null=True)
    quantity = models.FloatField(_('Quantidade'))
    send_date = models.DateField(_('Data Envio'))
    STATUS_CHOICES = (
        (1, _('Em Estoque')),
        (2, _('Enviado')),
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


class Tracking(models.Model):
    id = BigAutoField(primary_key=True)
    track_number = models.CharField(_('Rastreamento'), max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
