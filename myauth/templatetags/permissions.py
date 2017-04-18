from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter
def can_view_admin(user):
    return user.has_perm('myauth.view_admin')


@register.filter
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return group in user.groups.all()
