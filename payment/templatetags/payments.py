from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
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
