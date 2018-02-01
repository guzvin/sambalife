from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django.contrib.admin.templatetags.admin_list import result_list, pagination
from django import template
from django.template.loader import get_template
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
    return set(user.groups.all()) & set(kwargs.pop('lot').groups.all())

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


pagination_template = get_template('admin/store/lotreport/pagination.html')
register.inclusion_tag(pagination_template)(pagination)

result_list_template = get_template('admin/store/lotreport/change_list_results.html')
register.inclusion_tag(result_list_template)(result_list)
