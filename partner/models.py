from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger('django')


class Partner(models.Model):
    id = BigAutoField(primary_key=True)
    identity = models.CharField(_('Sigla'), max_length=4)
    name = models.CharField(_('Nome'), max_length=100)
    cost = models.DecimalField(_('Valor do Parceiro'), max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _('Parceiro')
        verbose_name_plural = _('Parceiros')

    def __str__(self):
        return self.name
