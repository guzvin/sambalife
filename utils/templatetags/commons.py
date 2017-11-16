from django import template

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