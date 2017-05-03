from django import template

register = template.Library()


@register.simple_tag
def check_status(item, status):
    return 'checked="checked"' if str(item.status) == status else ''


@register.simple_tag
def select_status(item, status):
    return 'selected="selected"' if str(item.status) == status else ''
