from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ShipmentConfig(AppConfig):
    name = 'shipment'
    verbose_name = _('Envio')
