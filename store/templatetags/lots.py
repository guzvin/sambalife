from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django import template
from utils.cron import check_lifecycle_one_day, check_lifecycle_three_days
import datetime
import logging

logger = logging.getLogger('django')

register = template.Library()


@register.filter
def has_store_perm(user, perm):
    return user.has_perm('.'.join(('store', perm)))


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def my_submit_row(context, lot):
    ctx = original_submit_row(context)
    if lot and lot.status == 2 and lot.payment_complete:
        ctx.update({
            'show_save': False,
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'show_delete_link': False,
            'show_delete': False,
        })
    return ctx


@register.simple_tag
def calculate_buy_price(product):
    product_redirect_cost = 0
    for redirect_service in product.redirect_services.all():
        product_redirect_cost += redirect_service.price
    return product.buy_price + product_redirect_cost


@register.simple_tag
def is_subscriber(user, **kwargs):
    lot = kwargs.pop('lot')
    return set(user.groups.all()) & set(lot.groups.all()) or (lot.lifecycle_open and user.is_authenticated)

stars_map = {
    1: 'um',
    2: 'dois',
    3: 'tres',
    4: 'quatro',
    5: 'cinco',
}


@register.simple_tag
def stars(number_stars):
    try:
        return stars_map[number_stars]
    except KeyError:
        return ''


@register.filter
def exists_lot_associated(product):
    if product.lot_product:
        return product.lot_product.lot.id
    return None


@register.simple_tag
def total_voi_roi(profit, cost):
    return profit / cost * 100


@register.simple_tag
def is_vip(lot):
    return not lot.lifecycle_open


@register.simple_tag
def lot_countdown(user, lot):
    return calculate_countdown(user, lot)


def calculate_countdown(user, lot, force_is_open=False):
    if force_is_open:
        current_date = datetime.datetime.now(datetime.timezone.utc)
        if lot.lifecycle_open:
            if check_lifecycle_three_days(current_date, lid=lot.id):
                lot.lifecycle = 3
        elif check_lifecycle_one_day(current_date, lid=lot.id):
            lot.lifecycle_open = True
    if lot.status == 1 and lot.lifecycle == 2 and lot.lifecycle_date and user.is_authenticated:
        # and is_subscriber(user, **{'lot': lot}):
        if lot.lifecycle_open:
            delta = 3
        else:
            delta = 1
        tdelta = lot.lifecycle_date + datetime.timedelta(days=delta)
        # tdelta = lot.lifecycle_date + datetime.timedelta(minutes=delta)
        return datetime.datetime.strftime(tdelta, '%b %-d, %Y %H:%M:%S')
    return None
