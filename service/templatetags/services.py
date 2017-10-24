from django import template

register = template.Library()


@register.filter
def has_service_perm(user, perm):
    return user.has_perm('.'.join(('service', perm)))
