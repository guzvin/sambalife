from django import template

register = template.Library()


@register.filter
def has_shipment_perm(user, perm):
    return user.has_perm('.'.join(('shipment', perm)))
