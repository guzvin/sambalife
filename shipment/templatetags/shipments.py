from django import template
from shipment.models import Package

register = template.Library()


@register.filter
def has_shipment_perm(user, perm):
    return user.has_perm('.'.join(('shipment', perm)))


@register.simple_tag
def status_bar(item):
    if item.status == 1:
        return 'emanalise'
    elif item.status == 2:
        return 'pgtaut'
    elif item.status == 3:
        return 'uplaut'
    elif item.status == 4:
        return 'analisef'
    elif item.status == 5:
        return 'enviado'


@register.simple_tag
def unit_weight_display(unit, **kwargs):
    k, v, a = Package.UNITS_WEIGHT_CHOICES[unit - 1]
    return a if 'abbreviate' in kwargs and kwargs['abbreviate'] else v


@register.simple_tag
def unit_length_display(unit, **kwargs):
    k, v, a = Package.UNITS_LENGTH_CHOICES[unit - 1]
    return a if 'abbreviate' in kwargs and kwargs['abbreviate'] else v
