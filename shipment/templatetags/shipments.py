from django import template
from shipment.models import Package, Estimates, Shipment
from django.db.models import Q
from django.utils import translation
from myauth.templatetags.users import has_user_perm
from datetime import timedelta
from utils.templatetags.commons import timezone_name
import pytz
import logging

logger = logging.getLogger('django')

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


@register.simple_tag
def render_payment_button(paypal_form, data):
    return paypal_form.render_button(data=data)


@register.simple_tag
def etc(initial_date, **kwargs):
    if initial_date is None or 'estimate' not in kwargs:
        return None
    try:
        estimates = Estimates.objects.first()
        if estimates and kwargs['estimate'] == 'preparation':
            delta_t = estimates.preparation
        elif estimates and kwargs['estimate'] == 'shipment':
            delta_t = estimates.shipment
        else:
            return None
        tz = pytz.timezone(timezone_name(translation.get_language()))
        etc_date = initial_date.astimezone(tz) + timedelta(hours=delta_t)
        logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@TIMEZONE DATE@@@@@@@@@@@@@@@@@@@@')
        logger.debug(etc_date)
        if estimates.weekends is False:
            etc_weekday = etc_date.weekday()
            if etc_weekday == 5:
                etc_date += timedelta(days=2)
            elif etc_weekday == 6:
                etc_date += timedelta(days=1)
        return etc_date
    except Estimates.DoesNotExist:
        return None


@register.simple_tag
def open_fba_shipments(user):
    query_filter = Q(status__lt=5) & Q(is_archived=False) & Q(is_canceled=False) & Q(type=None)
    if has_user_perm(user, 'view_users') is False:
        query_filter &= Q(user=user)
    return Shipment.objects.filter(query_filter).count()


@register.simple_tag
def open_mf_shipments(user):
    query_filter = Q(status__lt=5) & Q(is_archived=False) & Q(is_canceled=False) & ~Q(type=None)
    if has_user_perm(user, 'view_users') is False:
        query_filter &= Q(user=user)
    return Shipment.objects.filter(query_filter).count()
