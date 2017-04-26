from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from shipment.templatetags.shipments import has_shipment_perm
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden
from django.utils.translation import ugettext as _
from product.models import Product as OriginalProduct
from shipment.models import Shipment, Product, Package
from django.forms import modelformset_factory, inlineformset_factory, Field
from django.forms.widgets import Widget
from django.utils.html import conditional_escape, format_html, html_safe
from django.forms.utils import flatatt
from utils.helper import MyBaseInlineFormSet
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
def shipment_list(request):
    return render(request, 'shipment_list.html')


@login_required
@require_http_methods(["GET"])
def shipment_details(request, pid=None):
    return render(request, 'shipment_details.html')


class InlineProductWidget(Widget):
    def render(self, name, value, attrs=None):
        if value is None:
            hidden_value = ''
        else:
            hidden_value = value.id
        final_attrs = self.build_attrs(attrs, type='hidden', name=name)
        if hidden_value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = hidden_value
        hidden_tag = format_html('<input{} />', flatatt(final_attrs))
        html_fragment = format_html('<td>{}{}</td><td>{}</td><td>{}</td>',
                                    hidden_tag,
                                    value.id if value else '',
                                    value.name if value else '',
                                    value.description if value else '')
        return html_fragment


def my_formfield_callback(f, **kwargs):
    form_class = kwargs.pop('form_class', None)
    if form_class is None:
        return f.formfield(**kwargs)
    return form_class(**kwargs)


@login_required
@require_http_methods(["GET", "POST"])
def shipment_add_edit(request, pid=None):
    if has_shipment_perm(request.user, 'add_shipment') is False:
        return HttpResponseForbidden()
    if request.method == 'POST':
        preselected_products = request.POST.getlist('shipment_product')
        original_products = OriginalProduct.objects.filter(user=request.user, status=2, quantity__gt=0,
                                                           pk__in=preselected_products).order_by('id')
    else:
        original_products = OriginalProduct.objects.none()
    ShipmentFormSet = modelformset_factory(Shipment, fields=('send_date', 'pdf_1', 'pdf_2',),
                                           localized_fields=('send_date',), min_num=1, max_num=1)
    ProductFormSet = inlineformset_factory(Shipment, Product, formset=MyBaseInlineFormSet, fields=('quantity',
                                                                                                   'product'),
                                           field_classes={'product': Field},
                                           widgets={'product': InlineProductWidget},
                                           formfield_callback=my_formfield_callback,
                                           extra=original_products.count())
    kwargs = {'addText': _('Adicionar produto'), 'deleteText': _('Remover produto')}
    shipment_formset = ShipmentFormSet(queryset=Shipment.objects.none())
    product_formset = ProductFormSet(prefix='product_set', **kwargs)
    for subform, data in zip(product_formset.forms, original_products):
        subform.initial = {
            'quantity': None,
            'product': data
        }
    return render(request, 'shipment_add_edit.html', {'title': _('Envio'), 'shipment_formset': shipment_formset,
                                                      'product_formset': product_formset})
