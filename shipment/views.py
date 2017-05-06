from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from shipment.templatetags.shipments import has_shipment_perm
from myauth.templatetags.users import has_user_perm
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import string_concat,  ugettext as _
from product.models import Product as OriginalProduct
from shipment.models import Shipment, Product, Package, CostFormula
from django.contrib.sites.models import Site
from django.forms import modelformset_factory, inlineformset_factory, Field, DateField
from django.forms.widgets import Widget, FileInput
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.db import transaction
from django.utils import formats
from django.utils.encoding import force_text
from django.template import loader, Context
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from utils.helper import MyBaseInlineFormSet, send_email, ObjectView
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from utils.helper import Calculate
import magic
import json
import os
import logging

logger = logging.getLogger('django')


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
        hidden_tag = format_html('<input{} class="inline-row-key"/>', flatatt(final_attrs))
        html_fragment = format_html('<td>{}{}</td><td>{}</td><td>{}</td>',
                                    hidden_tag,
                                    value.id if value else '',
                                    value.name if value else '',
                                    value.description if value else '')
        return html_fragment

    def value_from_datadict(self, data, files, name):
        logger.debug('@@@@@@@@@@@@ VALUE FROM DICT @@@@@@@@@@@@@@')
        logger.debug(data.get(name))
        try:
            return OriginalProduct.objects.get(pk=data.get(name))
        except OriginalProduct.DoesNotExist:
            return data.get(name)


def my_formfield_callback(f, **kwargs):
    form_class = kwargs.pop('form_class', None)
    if form_class is None:
        return f.formfield(**kwargs)
    return form_class(**kwargs)


@login_required
@require_http_methods(["GET"])
def shipment_list(request):
    if has_shipment_perm(request.user, 'view_shipments'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        queries = []
        logger.debug('@@@@@@@@@@@@ SHIPMENT FILTERS @@@@@@@@@@@@@@')
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_values = {
            'status': '',
        }
        filter_send_date = request.GET.get('date')
        logger.debug(str(filter_send_date))
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if is_user_perm and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        if filter_send_date:
            queries.append(Q(send_date=DateField().to_python(filter_send_date)))
            filter_values['date'] = filter_send_date
        logger.debug(str(queries))
        logger.debug(str(len(queries)))
        if is_user_perm is False:
            queries.append(Q(user=request.user))
        is_filtered = len(queries) > 0
        if is_filtered:
            query = queries.pop()
            for item in queries:
                query &= item
            logger.debug(str(query))
        if is_user_perm:
            if is_filtered:
                logger.debug('FILTERED')
                _shipment_list = Shipment.objects.filter(query).select_related('user').order_by('id')
            else:
                logger.debug('ALL')
                _shipment_list = Shipment.objects.all().select_related('user').order_by('id')
        else:
            _shipment_list = Shipment.objects.filter(query).order_by('id')
    else:
        _shipment_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(_shipment_list, 10)
    try:
        shipments = paginator.page(page)
    except PageNotAnInteger:
        shipments = paginator.page(1)
    except EmptyPage:
        shipments = paginator.page(paginator.num_pages)
    return render(request, 'shipment_list.html', {'title': _('Estoque'), 'shipments': shipments,
                                                  'filter_values': ObjectView(filter_values)})


@login_required
@require_http_methods(["GET", "POST"])
def shipment_details(request, pid=None):
    if has_shipment_perm(request.user, 'view_shipments'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        query = Q(pk=pid)
        try:
            if is_user_perm is False:
                query &= Q(user=request.user)
                _shipment_details = Shipment.objects.get(query)
            else:
                _shipment_details = Shipment.objects.select_related('user').get(query)
        except Shipment.DoesNotExist:
            return HttpResponseBadRequest()
        _shipment_products = Product.objects.filter(shipment=_shipment_details).select_related('product').order_by('id')
        title = ' '.join([str(_('Envio')), str(_shipment_details.id)])
        context_data = {'title': title, 'shipment': _shipment_details, 'products': _shipment_products}
        if request.method == 'POST':
            if request.POST.get('add_shipment_package'):
                if has_shipment_perm(request.user, 'add_package'):
                    add_package_response = shipment_add_package(request, pid)
                    if isinstance(add_package_response, HttpResponse):
                        return add_package_response
                    context_data['packages'] = add_package_response
                else:
                    return HttpResponseForbidden()
            else:
                return HttpResponseBadRequest()
        elif request.GET.get('s') == '1' and has_shipment_perm(request.user, 'add_package'):
            context_data['success'] = True
            context_data['success_message'] = _('Pacote(s) inserido(s) com sucesso.')
        if _shipment_details.status == 1:  # Preparando para Envio
            if has_shipment_perm(request.user, 'add_package'):
                serialized_products = serializers.serialize('json', _shipment_products, fields=('id', 'quantity',
                                                                                                'product',))
                logger.debug('@@@@@@@@@@@@@@@ SERIALIZED PRODUCTS @@@@@@@@@@@@@@@@@')
                logger.debug(serialized_products)
                request.session['shipment_products'] = serialized_products
                if 'packages' not in context_data:
                    PackageFormSet = inlineformset_factory(Shipment, Package, formset=MyBaseInlineFormSet,
                                                           fields=('weight', 'height', 'width', 'depth',),
                                                           extra=1)
                    kwargs = {'addText': _('Adicionar pacote'), 'deleteText': _('Remover pacote')}
                    package_formset = PackageFormSet(instance=_shipment_details, prefix='package_set', **kwargs)
                    context_data['packages'] = package_formset
        else:
            _shipment_packages = Package.objects.filter(shipment=_shipment_details).order_by('id')
            context_data['packages'] = _shipment_packages
        logger.debug(context_data)
        return render(request, 'shipment_details.html', context_data)
    return HttpResponseForbidden()


def shipment_add_package(request, pid=None):
    if has_shipment_perm(request.user, 'view_shipments') is False or \
                    has_shipment_perm(request.user, 'add_package') is False:
        return HttpResponseForbidden()
    logger.debug('@@@@@@@@@@@@ ADD PACKAGE @@@@@@@@@@@@@@')
    custom_error_messages = {'required': _('Campo obrigatório.'), 'invalid': _('Informe um número maior que zero.')}
    PackageFormSet = inlineformset_factory(Shipment, Package, formset=MyBaseInlineFormSet,
                                           fields=('weight', 'height', 'width', 'depth',),
                                           extra=1,
                                           error_messages={'weight': custom_error_messages,
                                                           'height': custom_error_messages,
                                                           'width': custom_error_messages,
                                                           'depth': custom_error_messages})
    kwargs = {'addText': _('Adicionar pacote'), 'deleteText': _('Remover pacote'), 'allowEmptyForm': False}
    try:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().get(pk=pid, status=1)
            package_formset = PackageFormSet(request.POST, instance=shipment, prefix='package_set', **kwargs)
            if package_formset.is_valid():
                for package_form in package_formset:
                    package = package_form.save(commit=False)
                    logger.debug(package.shipment.id)
                    logger.debug(pid)
                    if force_text(package.shipment.id) != force_text(pid):
                        raise Shipment.DoesNotExist('Inconsistent data.')
                    shipment.status = 2
                    shipment_products = Product.objects.filter(shipment=shipment)
                    session_products = request.session.pop('shipment_products', '[]')
                    session_products = json.loads(session_products)
                    logger.debug(str(len(shipment_products)))
                    logger.debug(str(len(session_products)))
                    if len(shipment_products) != len(session_products):
                        raise Product.DoesNotExist('Inconsistent data.')
                    shipment.save(update_fields=['status'])
                    break
                package_formset.save()
                return HttpResponseRedirect('%s?s=1' % reverse('shipment_details', args=[pid]))
        return package_formset
    except (Product.DoesNotExist, Shipment.DoesNotExist) as err:
        logger.error(err)
        return HttpResponseBadRequest()


@login_required
@require_http_methods(["DELETE"])
def shipment_delete_product(request):
    if has_shipment_perm(request.user, 'change_shipment') is False:
        return HttpResponseForbidden()
    request.DELETE = QueryDict(request.body)
    logger.debug('@@@@@@@@@@@@ DELETE PRODUCT @@@@@@@@@@@@@@')
    try:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().get(pk=request.DELETE.get('delete_product_shipment_id'),
                                                                status=1)
            product = Product.objects.get(pk=request.DELETE.get('delete_product_product_id'),
                                          shipment=shipment)
            original_product = product.product
            logger.debug(product.quantity)
            logger.debug(original_product.quantity)
            shipment.total_products -= product.quantity
            http_response, cost = _shipment_calculate(shipment.total_products)
            shipment.cost = cost
            original_product.quantity += product.quantity
            deleted = product.delete()
            if deleted[0] == 0:
                raise Product.DoesNotExist('Delete did not affect any row.')
            shipment.save(update_fields=['total_products', 'cost'])
            original_product.save(update_fields=['quantity'])
    except (Product.DoesNotExist, Shipment.DoesNotExist) as err:
        logger.error(err)
        return HttpResponseBadRequest()
    return http_response


@login_required
@require_http_methods(["GET", "POST"])
def shipment_add(request):
    if has_shipment_perm(request.user, 'add_shipment') is False:
        return HttpResponseForbidden()
    if request.method == 'POST':
        if request.POST.get('save_shipment') is None:
            preselected_products = request.POST.getlist('shipment_product')
            original_products = OriginalProduct.objects.filter(user=request.user, status=2, quantity__gt=0,
                                                               pk__in=preselected_products).order_by('id')
        else:
            original_products = OriginalProduct.objects.none()
    else:
        original_products = OriginalProduct.objects.none()
    ShipmentFormSet = modelformset_factory(Shipment, fields=('send_date', 'pdf_1', 'pdf_2',),
                                           localized_fields=('send_date',), min_num=1, max_num=1,
                                           widgets={'pdf_1': FileInput(attrs={'class': 'form-control pdf_1-validate'})})
    ProductFormSet = inlineformset_factory(Shipment, Product, formset=MyBaseInlineFormSet, fields=('quantity',
                                                                                                   'product'),
                                           field_classes={'product': Field},
                                           widgets={'product': InlineProductWidget},
                                           formfield_callback=my_formfield_callback,
                                           extra=original_products.count())
    kwargs = {'addText': _('Adicionar produto'), 'deleteText': _('Remover produto')}
    logger.debug('@@@@@@@@@@@@ REQUEST METHOD @@@@@@@@@@@@@@')
    logger.debug(request.method)
    if request.method == 'GET' and request.GET.get('s') == '1':
        return render(request, 'shipment_add.html', {'title': _('Envio'), 'success': True,
                                                     'success_message': _('Envio inserido com sucesso.'),
                                                     'shipment_formset':
                                                         ShipmentFormSet(queryset=Shipment.objects.none()),
                                                     'product_formset':
                                                         ProductFormSet(prefix='product_set', **kwargs)})
    logger.debug(str(request.method == 'POST' and request.POST.get('save_shipment')))
    if request.method == 'POST' and request.POST.get('save_shipment'):
        shipment_formset = ShipmentFormSet(request.POST, request.FILES, queryset=Shipment.objects.none())
        product_formset = ProductFormSet(request.POST, prefix='product_set', **kwargs)
        shipment_formset_is_valid = shipment_formset.is_valid()
        product_formset_is_valid = product_formset.is_valid()
        if shipment_formset_is_valid and product_formset_is_valid:
            with transaction.atomic():
                for shipment_form in shipment_formset:
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVE PROCESS @@@@@@@@@@@@@@')
                    shipment = shipment_form.save(commit=False)
                    shipment.user = request.user
                    shipment.status = 1  # Preparing for Shipment
                    shipment.total_products = 0
                    products = product_formset.save(commit=False)
                    for product in products:
                        original_product = OriginalProduct.objects.get(pk=product.product.id)
                        original_product.quantity -= product.quantity
                        original_product.save()
                        shipment.total_products += product.quantity
                    cost_formula = CostFormula.objects.all()
                    if len(cost_formula) > 0:
                        cost = Calculate().evaluate(cost_formula[0].formula, variables={'x': shipment.total_products})
                    else:
                        cost = shipment.total_products * 1.25
                    if cost > 0:
                        shipment.cost = cost
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVE @@@@@@@@@@@@@@')
                    shipment.save()
                    product_formset.instance = shipment
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVED @@@@@@@@@@@@@@')
                    product_formset.save()
                    logger.debug('@@@@@@@@@@@@ SEND PDF 1 EMAIL @@@@@@@@@@@@@@')
                    send_add_shipment_email(request, shipment, products)
            return HttpResponseRedirect('%s?s=1' % reverse('shipment_add'))
        else:
            logger.warning('@@@@@@@@@@@@ FORM ERRORS @@@@@@@@@@@@@@')
            logger.warning(shipment_formset.errors)
            logger.warning(product_formset.errors)
    else:
        shipment_formset = ShipmentFormSet(queryset=Shipment.objects.none())
        product_formset = ProductFormSet(prefix='product_set', **kwargs)
        for subform, data in zip(product_formset.forms, original_products):
            subform.initial = {
                'quantity': data.quantity,
                'product': data
            }
    return render(request, 'shipment_add.html', {'title': _('Envio'), 'shipment_formset': shipment_formset,
                                                 'product_formset': product_formset})


@login_required
@require_http_methods(["GET"])
def shipment_calculate(request):
    if has_shipment_perm(request.user, 'add_shipment') is False:
        return HttpResponseForbidden()
    http_response, cost = _shipment_calculate(request.GET.get('items'))
    return http_response


def _shipment_calculate(items):
    cost_formula = CostFormula.objects.all()
    if len(cost_formula) > 0:
        cost = Calculate().evaluate(cost_formula[0].formula, variables={'x': items})
    else:
        cost = items * 1.25
    return HttpResponse(json.dumps({'cost': force_text(formats.number_format(cost, use_l10n=True,
                                                                             decimal_pos=2)),
                                    'items': items}),
                        content_type='application/json'), cost


@login_required
@require_http_methods(["GET"])
def shipment_pdf_1(request, pid=None):
    try:
        shipment = Shipment.objects.get(pk=pid)
    except Shipment.DoesNotExist:
        return HttpResponseBadRequest()
    if shipment.user == request.user or request.user.groups.filter(name='admins').exists():
        content_type = magic.from_file(os.path.sep.join([settings.MEDIA_ROOT, shipment.pdf_1.name]), mime=True)
        filename = shipment.pdf_1.name.split('/')[-1]
        logger.debug('@@@@@@@@@@@@ FILE CONTENT TYPE @@@@@@@@@@@@@@')
        logger.debug(filename)
        logger.debug(content_type)
        response = HttpResponse(shipment.pdf_1, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
    else:
        return HttpResponseForbidden()


def send_add_shipment_email(request, shipment, products):
    message = loader.get_template('email/add-shipment.html').render(
        Context({'user_name': request.user.first_name, 'protocol': 'https',
                 'domain': Site.objects.get_current().domain, 'shipment': shipment, 'products': products}))
    str1 = _('Cadastro de Envio %(number)s') % {'number': shipment.id}
    str2 = _('Vendedor Online Internacional')
    user_model = get_user_model()
    admins = user_model.objects.filter(groups__name='admins')
    admins_email = [user.email for user in admins]
    logger.debug('@@@@@@@@@@@@ ADMINS EMAIL @@@@@@@@@@@@@@')
    logger.debug(admins_email)
    send_email(string_concat(str1, ' ', str2), message, [request.user.email], bcc=admins_email)
