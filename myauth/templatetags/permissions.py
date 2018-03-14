from django import template

register = template.Library()


@register.filter
def can_view_admin(user):
    return user.has_perm('myauth.view_admin')


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
