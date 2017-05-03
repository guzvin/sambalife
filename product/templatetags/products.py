from django import template

register = template.Library()


@register.filter
def has_product_perm(user, perm):
    return user.has_perm('.'.join(('product', perm)))
