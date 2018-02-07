from django.contrib.admin.templatetags.admin_list import result_list, pagination
from django.template.loader import get_template
from django import template

register = template.Library()


pagination_template = get_template('admin/store/lotreport/pagination.html')
register.inclusion_tag(pagination_template)(pagination)

result_list_template = get_template('admin/store/lotreport/change_list_results.html')
register.inclusion_tag(result_list_template)(result_list)