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
    return 'Brazil/East' if lang == 'pt-br' else 'US/Eastern'
