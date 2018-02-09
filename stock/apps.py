from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class StockConfig(AppConfig):
    name = 'stock'
    verbose_name = _('Estoque')
