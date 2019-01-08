from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from payment.models import Subscribe
import logging

logger = logging.getLogger('django')


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def my_submit_row(context):
    ctx = original_submit_row(context)
    logger.debug('@@@@@@@@@@@@ SUBMIT ROW @@@@@@@@@@@@')
    logger.debug(ctx)
    ctx.update({
        'show_save': False,
        'show_save_and_add_another': False,
        'show_save_and_continue': False
    })
    logger.debug('@@@@@@@@@@@@ MY SUBMIT ROW @@@@@@@@@@@@')
    logger.debug(ctx)
    return ctx


@register.simple_tag
def is_subscriber_voiprime(user):
    if user.is_authenticated:
        return Subscribe.objects.filter(user=user, plan_type=1, is_active=True).exists()
    return False


@register.simple_tag
def is_subscriber_wcyazs(user):
    if user.is_authenticated:
        return Subscribe.objects.filter(user=user, plan_type=2, is_active=True).exists()
    return False
