from django.db import models
from django.utils.translation import ugettext_lazy as _


class Params(models.Model):
    id = models.AutoField(primary_key=True)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2, default=0.99)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2, default=0.30)
    partner_cost = models.DecimalField(_('Valor do Parceiro'), max_digits=12, decimal_places=2, default=0.20)
    redirect_factor = models.DecimalField(_('Valor Base'), max_digits=12, decimal_places=2, default=1.29)
    time_period_one = models.SmallIntegerField(_('Período Base'), null=True, blank=True,
                                               default=30, help_text=_('Em dias.'))
    redirect_factor_two = models.DecimalField(_('Valor do Segundo Período'), max_digits=12, decimal_places=2,
                                              null=True, blank=True, default=1.49)
    time_period_two = models.SmallIntegerField(_('Segundo Período'), null=True, blank=True, default=15,
                                               help_text=_('Em dias. Após o primeiro período.'))
    redirect_factor_three = models.DecimalField(_('Valor do Terceiro Período'), max_digits=12, decimal_places=2,
                                                null=True, blank=True, default=1.99)
    time_period_three = models.SmallIntegerField(_('Terceiro Período'), null=True, blank=True, default=15,
                                                 help_text=_('Em dias. Após o segundo período.'))

    class Meta:
        verbose_name = _('Parametrizações')
        verbose_name_plural = _('Parametrizações')

    def __str__(self):
        return str(_('Parametrizações'))
