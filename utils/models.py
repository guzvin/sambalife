from django.db import models
from django.utils.translation import ugettext_lazy as _


class Params(models.Model):
    id = models.AutoField(primary_key=True)
    redirect_factor = models.DecimalField(_('Valor do Redirecionamento'), max_digits=12, decimal_places=2, default=1.29)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2, default=0.99)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2, default=0.30)

    class Meta:
        verbose_name = _('Parametrizações')
        verbose_name_plural = _('Parametrizações')

    def __str__(self):
        return str(_('Parametrizações'))
