from django import template

register = template.Library()


@register.filter
def has_product_perm(user, perm):
    return user.has_perm('.'.join(('product', perm)))


@register.simple_tag
def check_status(product, status):
    return 'checked="checked"' if str(product.status) == status else ''


@register.simple_tag
def select_status(product, status):
    return 'selected="selected"' if str(product.status) == status else ''
