from django import template
from store.templatetags.lots import has_store_perm
import logging

logger = logging.getLogger('django')

register = template.Library()


@register.simple_tag
def check_status(item, status):
    return 'checked="checked"' if str(item.status) == status else ''


@register.simple_tag
def select_status(item, status):
    return 'selected="selected"' if str(item.status) == status else ''


@register.simple_tag
def select_condition(item, condition):
    return 'selected="selected"' if str(item) == condition else ''


@register.simple_tag
def timezone_name(lang):
    return 'Brazil/East' if lang == 'pt' else 'US/Eastern'


@register.simple_tag
def render_payment_button(paypal_form, data):
    return paypal_form.render_button(data=data)


@register.filter
def startswith(text, starts):
    if isinstance(text, (str, bytes)):
        return text.startswith(starts)
    return False


@register.simple_tag
def log_message(message):
    logger.debug(message)
    return ''


@register.simple_tag
def assign(value):
    return value


@register.filter
def check_collaborator(collaborator, user):
    if has_store_perm(user, 'collaborator'):
        return user.collaborator and collaborator == user.collaborator_id
    return True


@register.filter
def is_collaborator(collaborator, user):
    if has_store_perm(user, 'collaborator'):
        return user.collaborator and collaborator == user.collaborator_id
    return False
