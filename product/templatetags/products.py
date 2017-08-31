from django import template
from shipment.models import Product
from django.db.models import Q
import datetime

register = template.Library()


@register.filter
def has_product_perm(user, perm):
    return user.has_perm('.'.join(('product', perm)))


@register.filter
def exists_shipment_associated(product):
    products = Product.objects.filter(Q(product__id=product.id) & ~Q(shipment__status=5) &
                                      Q(shipment__is_archived=False) &
                                      Q(shipment__is_canceled=False)).order_by('shipment_id')
    return ', '.join([str(product.shipment_id) for product in products])


@register.filter
def days_in_stock(product, max_time_period):
    elapsed = datetime.datetime.now(datetime.timezone.utc) - product.receive_date
    elapsed = elapsed.days
    return elapsed if elapsed <= max_time_period else ''.join([str(max_time_period), '+'])
