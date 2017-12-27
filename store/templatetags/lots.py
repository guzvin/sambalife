from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django import template
import logging

logger = logging.getLogger('django')

register = template.Library()


@register.filter
def has_store_perm(user, perm):
    return user.has_perm('.'.join(('store', perm)))


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def my_submit_row(context, lot):
    ctx = original_submit_row(context)
    if lot and lot.status == 2:
        ctx.update({
            'show_save': False,
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'show_delete_link': False,
            'show_delete': False,
        })
    return ctx
