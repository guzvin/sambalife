from django import template
from django.template.loader import get_template
from django.contrib.admin.templatetags.admin_list import result_list, pagination

register = template.Library()


@register.filter
def has_user_perm(user, perm):
    return user.has_perm('.'.join(('myauth', perm)))

pagination_template = get_template('admin/myauth/userlotreport/pagination.html')
register.inclusion_tag(pagination_template)(pagination)

result_list_template = get_template('admin/myauth/userlotreport/change_list_results.html')
register.inclusion_tag(result_list_template)(result_list)
