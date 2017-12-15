from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from shipment.templatetags.shipments import has_shipment_perm
from myauth.templatetags.users import has_user_perm
from myauth.templatetags.permissions import has_group
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import ugettext as _, ungettext
from product.models import Product as OriginalProduct
from service.models import Service, Config
from shipment.models import Shipment, Product, Warehouse, Package, CostFormula
from django.forms import modelformset_factory, inlineformset_factory, Field, DateField
from django.forms.widgets import Widget, FileInput
from django.utils.html import format_html, mark_safe
from django.forms.utils import flatatt
from django.db import transaction
from django.utils import formats
from django.utils.encoding import force_text
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from utils import helper
from utils.models import Billing
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from payment.forms import MyPayPalSharedSecretEncryptedPaymentsForm
from shipment.templatetags.shipments import unit_weight_display, unit_length_display
from service.templatetags.services import has_service_perm
from django.contrib.auth import get_user_model
from django.template import loader, TemplateDoesNotExist
from shipment.templatetags.shipments import etc
from decimal import Decimal
import time
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
        html_fragment = format_html('<td>{}{}</td><td>{}</td><td>{}</td><td>{}</td>',
                                    hidden_tag,
                                    value.id if value else '',
                                    value.name if value else '',
                                    value.description if value else '',
                                    formats.date_format(value.best_before, "SHORT_DATE_FORMAT")
                                    if value and value.best_before else '')
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
    return list_shipment(request, 'shipment_list.html', has_shipment_perm(request.user, 'view_shipments'))


@login_required
@require_http_methods(["GET"])
def merchant_shipment_list(request):
    return list_shipment(request, 'merchant_shipment_list.html', has_shipment_perm(request.user, 'view_fbm_shipments'))


def list_shipment(request, template_name, has_perm):
    if has_perm:
        is_user_perm = has_user_perm(request.user, 'view_users')
        queries = []
        logger.debug('@@@@@@@@@@@@ SHIPMENT FILTERS @@@@@@@@@@@@@@')
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_archived = request.GET.get('archived')
        logger.debug(str(filter_archived))
        filter_canceled = request.GET.get('canceled')
        logger.debug(str(filter_canceled))
        filter_values = {
            'status': '',
        }
        filter_created_date = request.GET.get('date')
        logger.debug(str(filter_created_date))
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if is_user_perm and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user) |
                           Q(user__email__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        if filter_created_date:
            d = DateField().to_python(filter_created_date)
            queries.append(Q(created_date__date=d))
            filter_values['date'] = filter_created_date
        if filter_canceled and filter_canceled == 'on':
            filter_values['canceled'] = 'checked=checked'
        else:
            queries.append(Q(is_canceled=False))
        if filter_archived and filter_archived == 'on':
            filter_values['archived'] = 'checked=checked'
        elif filter_canceled and filter_canceled == 'on':
            queries.append(((Q(is_archived=False) & Q(is_canceled=False)) | Q(is_canceled=True)))
        else:
            queries.append(Q(is_archived=False))
        logger.debug(str(queries))
        logger.debug(str(len(queries)))
        if is_user_perm is False:
            queries.append(Q(user=request.user))
        if template_name == 'shipment_list.html':
            queries.append(Q(type=None))
        else:
            queries.append(~Q(type=None))
        query = queries.pop()
        for item in queries:
            query &= item
        logger.debug(str(query))
        if is_user_perm:
            logger.debug('FILTERED')
            _shipment_list = Shipment.objects.filter(query).select_related('user').order_by('id')
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
    context_data = {'title': _('Estoque'), 'shipments': shipments, 'filter_values': helper.ObjectView(filter_values),
                    'view_perm': has_perm}
    if request.GET.get('ra') == '1':
        context_data['custom_modal'] = True
        context_data['modal_title'] = _('Mensagem importante!')
        context_data['modal_message'] = _('O envio foi removido, pois seus produtos não estavam mais disponíveis em '
                                          'estoque.')
    return render(request, template_name, context_data)


@login_required
@require_http_methods(["GET", "POST"])
def shipment_details(request, pid=None):
    logger.debug('@@@@@@@@@@@@@@@ REMOTE ADDRESS @@@@@@@@@@@@@@@@@')
    logger.debug(request.META)
    if has_shipment_perm(request.user, 'view_shipments') or has_shipment_perm(request.user, 'view_fbm_shipments'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        query = Q(pk=pid)
        try:
            if is_user_perm is False:
                query &= Q(user=request.user)
            _shipment_details = Shipment.objects.select_related('user').get(query)
        except Shipment.DoesNotExist as e:
            logger.error(e)
            try:
                error_400_template = loader.get_template('error/400_shipment.html')
            except TemplateDoesNotExist:
                return HttpResponseBadRequest()
            return HttpResponseBadRequest(error_400_template.render())
        has_perm = _shipment_details.type and has_shipment_perm(request.user, 'view_fbm_shipments')
        if has_perm is False:
            has_perm = _shipment_details.type is None and has_shipment_perm(request.user, 'view_shipments')
        if has_perm is False:
            return HttpResponseForbidden()
        _shipment_products = Product.objects.filter(shipment=_shipment_details).select_related('product').order_by('id')
        billing = Billing.objects.first()
        if billing:
            billing_type = billing.type
        else:
            billing_type = 2  # por serviço
        ignored_response, cost = calculate_shipment(_shipment_products, _shipment_details.user.id)
        _shipment_details.cost = cost
        _shipment_warehouses = Warehouse.objects.filter(shipment=_shipment_details).order_by('id')
        title = ' '.join([str(_('Envio')), str(_shipment_details.id)])
        context_data = {'title': title, 'shipment': _shipment_details, 'products': _shipment_products,
                        'warehouses': _shipment_warehouses, 'billing_type': billing_type}
        custom_error_messages = {'required': _('Campo obrigatório.'), 'invalid': _('Informe um número maior que zero.')}

        ShipmentFormSet = modelformset_factory(Shipment, fields=('pdf_1',), min_num=1, max_num=1,
                                               widgets={'pdf_1': FileInput(attrs={'class': 'form-control input-70'})})

        PackageFormSet = inlineformset_factory(Shipment, Package, formset=helper.MyBaseInlineFormSet,
                                               fields=('warehouse', 'pick_ticket', 'weight', 'height', 'width',
                                                       'length', 'pdf_2', 'shipment_tracking'),
                                               extra=render_extra_package(_shipment_details),
                                               error_messages={'weight': custom_error_messages,
                                                               'height': custom_error_messages,
                                                               'width': custom_error_messages,
                                                               'length': custom_error_messages},
                                               widgets={'pdf_2': FileInput(
                                                   attrs={'class': 'form-control input-70 pdf_2-validate'})})
        package_formset = None
        if request.method == 'GET' and request.GET.get('s') == '2':
                context_data['success'] = True
                context_data['success_message'] = _('Alteração salva com sucesso.')
        elif request.method == 'POST' and _shipment_details.is_archived is False \
                and _shipment_details.is_canceled is False and _shipment_details.type is None \
                and _shipment_details.status < 5:
            shipment_formset = ShipmentFormSet(request.POST, request.FILES)
            logger.debug('@@@@@@@@@@@@@@@ UPLOAD PDF 1 @@@@@@@@@@@@@@@@@')
            logger.debug(shipment_formset.is_valid())
            logger.debug(shipment_formset.has_changed())
            if shipment_formset.is_valid() and shipment_formset.has_changed():
                shipment_formset.save()
                context_data['shipment_fs'] = shipment_formset
        if _shipment_details.is_archived is False and _shipment_details.is_canceled is False and \
                _shipment_details.status == 1:
            # Preparando para Envio
            if request.method == 'POST' and request.POST.get('add_shipment_package'):
                if has_shipment_perm(request.user, 'add_package'):
                    _shipment_details.information = request.POST.get('shipment_extra_info')

                    package_formset = shipment_add_status_one_data(request, PackageFormSet,
                                                                   _shipment_details.information, pid)
                    context_data['packages'] = package_formset
                else:
                    return HttpResponseForbidden()
            if has_shipment_perm(request.user, 'add_package'):
                if billing_type == 2 and has_service_perm(request.user, 'add_product'):
                    _services = Service.objects.all()
                    context_data['services'] = _services
                serialized_products = serializers.serialize('json', _shipment_products, fields=('id', 'quantity',
                                                                                                'product',))
                logger.debug('@@@@@@@@@@@@@@@ SERIALIZED PRODUCTS @@@@@@@@@@@@@@@@@')
                logger.debug(serialized_products)
                request.session['shipment_products'] = serialized_products
        elif _shipment_details.is_archived is False and _shipment_details.is_canceled is False:
            PackageFormSet.extra = 0
            PackageFormSet.max_num = 1
            ignore_package_fields = []
            if has_shipment_perm(request.user, 'add_package') is False:
                ignore_package_fields.append('warehouse')
                ignore_package_fields.append('pick_ticket')
                ignore_package_fields.append('weight')
                ignore_package_fields.append('height')
                ignore_package_fields.append('width')
                ignore_package_fields.append('length')
                ignore_package_fields.append('shipment_tracking')
            novalidate_fields = []
            if _shipment_details.status != 2:
                novalidate_fields.append('pdf_2')
            if _shipment_details.type:
                novalidate_fields.append('warehouse')
            package_kwargs = {'renderEmptyForm': False, 'noValidateFields': novalidate_fields}
            if billing_type == 2:
                _services = Service.objects.filter(product__product__shipment__user_id=_shipment_details.user_id).distinct()
                context_data['services'] = _services
            if _shipment_details.status == 3:
                # Pagamento Autorizado
                if request.user == _shipment_details.user or has_shipment_perm(request.user, 'add_package'):
                    if request.method == 'GET':
                        if request.GET.get('s') == '1':
                            package_formset = PackageFormSet(
                                queryset=Package.objects.filter(shipment=_shipment_details).order_by('id'),
                                instance=_shipment_details, prefix='package_set', **package_kwargs)
                            context_data['success'] = True
                            context_data['success_message'] = ungettext('Upload realizado com sucesso.',
                                                                        'Uploads realizados com sucesso.',
                                                                        len(package_formset))
                    elif request.method == 'POST':
                        package_formset = PackageFormSet(request.POST, request.FILES, instance=_shipment_details,
                                                         prefix='package_set', **package_kwargs)
                        if package_formset.is_valid() and package_formset.has_changed():
                            try:
                                if edit_warehouse(package_formset, pid, True, ignore_package_fields):
                                    # TODO ENVIAR EMAIL NO UPLOAD DE NOVO PDF
                                    return HttpResponseRedirect('%s?s=2' % reverse('shipment_details', args=[pid]))
                                else:
                                    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
                            except Shipment.DoesNotExist as e:
                                logger.error(e)
                                return HttpResponseBadRequest()
                if request.user == _shipment_details.user or has_group(request.user, 'admins'):
                    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(_shipment_details.user)
                    context_data['paypal_form'] = MyPayPalSharedSecretEncryptedPaymentsForm(is_sandbox=is_sandbox,
                                                                                            is_render_button=True)
            elif _shipment_details.status == 2:
                # Upload PDF 2 Autorizado
                if request.user == _shipment_details.user or has_group(request.user, 'admins') \
                        or has_shipment_perm(request.user, 'add_package'):
                    if request.method == 'GET':
                        if request.GET.get('s') == '1':
                            package_formset = PackageFormSet(
                                    queryset=Package.objects.filter(shipment=_shipment_details).order_by('id'),
                                    instance=_shipment_details, prefix='package_set', **package_kwargs)
                            context_data['success'] = True
                            context_data['success_message'] = ungettext('Pacote inserido com sucesso.',
                                                                        'Pacotes inseridos com sucesso.',
                                                                        len(package_formset))
                    elif request.method == 'POST' and request.POST.get('add_package_file'):
                        package_formset = PackageFormSet(request.POST, request.FILES, instance=_shipment_details,
                                                         prefix='package_set', **package_kwargs)
                        logger.debug('@@@@@@@@@@@@@@@ PDF 2 IS VALID @@@@@@@@@@@@@@@@@')
                        logger.debug(package_formset)
                        if package_formset.is_valid() and (request.user == _shipment_details.user
                                                           or has_shipment_perm(request.user, 'add_package')):
                            try:
                                with transaction.atomic():
                                    updated_rows = Shipment.objects.select_for_update().filter(query).update(status=3)
                                    if updated_rows == 0:
                                        logger.error('Zero rows updated.')
                                        raise Shipment.DoesNotExist('Zero rows updated.')
                                    for package_form in package_formset:
                                        package = package_form.save(commit=False)
                                        package_shipment_id = package.shipment.id
                                        logger.debug(package_shipment_id)
                                        logger.debug(pid)
                                        logger.debug(package_form.has_changed())
                                        if force_text(package_shipment_id) != force_text(pid):
                                            logger.error('Inconsistent data.')
                                            raise Shipment.DoesNotExist('Inconsistent data.')
                                        if has_shipment_perm(request.user, 'add_package'):
                                            package.save(update_fields=['warehouse', 'pick_ticket', 'pdf_2'])
                                        else:
                                            package.save(update_fields=['pdf_2'])
                            except Shipment.DoesNotExist as e:
                                logger.error(e)
                                return HttpResponseBadRequest()
                            send_email_shipment_payment(request, _shipment_details)
                            return HttpResponseRedirect('%s?s=1' % reverse('shipment_details', args=[pid]))
                        elif has_shipment_perm(request.user, 'add_package'):
                            novalidate_fields.append('pdf_2')
                            package_formset = PackageFormSet(request.POST, instance=_shipment_details,
                                                             prefix='package_set', **package_kwargs)
                            try:
                                if edit_warehouse(package_formset, pid, False, ignore_package_fields):
                                    return HttpResponseRedirect('%s?s=2' % reverse('shipment_details', args=[pid]))
                                else:
                                    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
                            except Shipment.DoesNotExist as e:
                                logger.error(e)
                                return HttpResponseBadRequest()
            elif _shipment_details.status == 4 or _shipment_details.status == 5:
                # Checagens Finais ou Enviado
                if request.method == 'GET':
                    if _shipment_details.status == 5:
                        if has_group(request.user, 'admins') and request.GET.get('s') == '1':
                            context_data['success'] = True
                            context_data['success_message'] = _('Envio concluído com sucesso.')
                else:
                    package_formset = PackageFormSet(request.POST, request.FILES, instance=_shipment_details,
                                                     prefix='package_set', **package_kwargs)
                    logger.debug('@@@@@@@@@@@@@ PACKAGE FORMSET VALIDATION @@@@@@@@@@@@@@@@@@@@@')
                    logger.debug(package_formset.is_valid())
                    logger.debug(package_formset.has_changed())
                    is_shipment_closed = _shipment_details.status > 4
                    if is_shipment_closed:
                        if 'pick_ticket' not in ignore_package_fields:
                            ignore_package_fields.append('pick_ticket')
                    if request.POST.get('add_package_tracking'):
                        if 'warehouse' not in ignore_package_fields:
                            ignore_package_fields.append('warehouse')
                        if 'weight' not in ignore_package_fields:
                            ignore_package_fields.append('weight')
                        if 'height' not in ignore_package_fields:
                            ignore_package_fields.append('height')
                        if 'width' not in ignore_package_fields:
                            ignore_package_fields.append('width')
                        if 'length' not in ignore_package_fields:
                            ignore_package_fields.append('length')
                    else:
                        if 'warehouse' not in ignore_package_fields:
                            ignore_package_fields.append('warehouse')
                        if 'weight' not in ignore_package_fields:
                            ignore_package_fields.append('weight')
                        if 'height' not in ignore_package_fields:
                            ignore_package_fields.append('height')
                        if 'width' not in ignore_package_fields:
                            ignore_package_fields.append('width')
                        if 'length' not in ignore_package_fields:
                            ignore_package_fields.append('length')
                        if 'shipment_tracking' not in ignore_package_fields:
                            ignore_package_fields.append('shipment_tracking')
                    if package_formset.is_valid():
                        form_has_changed = False
                        tracking_has_changed = False
                        is_completing_shipment = str(request.POST.get('complete_shipment')) == '1'
                        packages = []
                        try:
                            with transaction.atomic():
                                for package_form in package_formset:
                                    package = package_form.save(commit=False)
                                    if is_completing_shipment and package.shipment_tracking:
                                        packages.append(package)
                                    if package_form.has_changed() is False:
                                        continue
                                    update_fields_fields = list(
                                        set(package_form.changed_data).difference(set(ignore_package_fields)))
                                    if len(update_fields_fields) == 0:
                                        continue
                                    form_has_changed = True
                                    tracking_has_changed = 'shipment_tracking' in update_fields_fields \
                                        and is_shipment_closed if tracking_has_changed is False else True
                                    package_shipment_id = package.shipment.id
                                    logger.debug('@@@@@@@@@@@@@ PACKAGE FORM CHANGED DATA @@@@@@@@@@@@@@@@@@@@@')
                                    logger.debug(package_shipment_id)
                                    logger.debug(pid)
                                    logger.debug(package_form.has_changed())
                                    logger.debug(package_form.changed_data)
                                    if force_text(package_shipment_id) != force_text(pid):
                                        logger.error('Inconsistent data.')
                                        raise Shipment.DoesNotExist('Inconsistent data.')
                                    package.save(update_fields=update_fields_fields)
                                    if is_completing_shipment is False:
                                        packages.append(package)
                                previous_state = _shipment_details.status
                                if _shipment_details.status == 4 and has_group(request.user, 'admins') \
                                        and is_completing_shipment:
                                    _shipment_details.status = 5
                                    _shipment_details.save(update_fields=['status'])
                                    complete_shipment(_shipment_details)
                        except Shipment.DoesNotExist as e:
                            logger.error(e)
                            return HttpResponseBadRequest()
                        if previous_state != _shipment_details.status:
                            send_email_shipment_sent(request, _shipment_details, packages)
                            return HttpResponseRedirect('%s?s=1' % reverse('shipment_details', args=[pid]))
                        elif form_has_changed:
                            if tracking_has_changed:
                                send_email_shipment_change_shipment(request, _shipment_details, packages)
                            return HttpResponseRedirect('%s?s=2' % reverse('shipment_details', args=[pid]))
                        return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
        if package_formset is None:
            if has_shipment_perm(request.user, 'add_package') and _shipment_details.status == 1:
                package_kwargs = {'addText': _('Adicionar pacote'), 'deleteText': _('Remover pacote')}
                package_formset = PackageFormSet(instance=_shipment_details, prefix='package_set', **package_kwargs)
            elif _shipment_details.status > 1:
                PackageFormSet.extra = 0
                PackageFormSet.max_num = 1
                package_kwargs = {'renderEmptyForm': False}
                package_formset = PackageFormSet(
                    queryset=Package.objects.filter(shipment=_shipment_details).order_by('id'),
                    instance=_shipment_details, prefix='package_set', **package_kwargs)
        if package_formset and 'packages' not in context_data:
            context_data['packages'] = package_formset
        if 'shipment_fs' not in context_data:
            context_data['shipment_fs'] = ShipmentFormSet(
                queryset=Shipment.objects.select_related('user').filter(query))
        else:
            # send_email_shipment_change_shipment(request, _shipment_details, packages)
            return HttpResponseRedirect('%s?s=2' % reverse('shipment_details', args=[pid]))
        logger.debug(context_data)
        if _shipment_details.type:
            return render(request, 'merchant_shipment_details.html', context_data)
        else:
            return render(request, 'shipment_details.html', context_data)
    return HttpResponseForbidden()


def complete_shipment(_shipment_details):
    set_as_archived = []
    set_as_forwarded = []
    products = _shipment_details.product_set.all()
    for product in products:
        if Product.objects.filter(Q(product__id=product.product_id) &
                                  ~Q(shipment__id=_shipment_details.id) &
                                  ~Q(shipment__status=5) &
                                  Q(shipment__is_archived=False) &
                                  Q(shipment__is_canceled=False)).exists() is True:
            continue
        try:
            original_product = OriginalProduct.objects.get(pk=product.product_id)
            if original_product.quantity == original_product.quantity_partial and original_product.quantity == 0:
                set_as_archived.append(product.product_id)
            elif original_product.quantity != original_product.quantity_partial and \
                    original_product.quantity_partial == 0:
                set_as_forwarded.append(product.product_id)
        except OriginalProduct.DoesNotExist:
            pass
    if set_as_archived:
        OriginalProduct.objects.filter(id__in=set_as_archived).update(status=99)
    if set_as_forwarded:
        OriginalProduct.objects.filter(id__in=set_as_forwarded).update(status=1)


def render_extra_package(_shipment_details):
    logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@ render extra package')
    package_exists = Package.objects.filter(shipment=_shipment_details).exists()
    logger.debug(package_exists)
    extra_package = 1 if package_exists is False else 0
    logger.debug(extra_package)
    return extra_package


def current_milli_time(): return int(round(time.time() * 1000))


@login_required
@require_http_methods(["GET"])
def shipment_pay_form(request, pid=None):
    if has_shipment_perm(request.user, 'view_shipments') or has_shipment_perm(request.user, 'view_fbm_shipments'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        query = Q(pk=pid) & Q(status=3) & Q(is_archived=False) & Q(is_canceled=False)
        try:
            with transaction.atomic():
                if is_user_perm is False:
                    query &= Q(user=request.user)
                _shipment_details = Shipment.objects.select_for_update().select_related('user').get(query)
                if request.user == _shipment_details.user or has_group(request.user, 'admins'):
                    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(_shipment_details.user)
                    if is_sandbox:
                        invoice_id = '_'.join(['A', str(request.user.id), str(pid), 'debug', str(current_milli_time())])
                        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX
                        paypal_cert_id = settings.PAYPAL_CERT_ID_SANDBOX
                        paypal_cert = settings.PAYPAL_CERT_SANDBOX
                    else:
                        invoice_id = '_'.join(['A', str(request.user.id), str(pid)])
                        paypal_business = settings.PAYPAL_BUSINESS
                        paypal_cert_id = settings.PAYPAL_CERT_ID
                        paypal_cert = settings.PAYPAL_CERT

                    paypal_private_cert = settings.PAYPAL_PRIVATE_CERT
                    paypal_public_cert = settings.PAYPAL_PUBLIC_CERT

                    _shipment_products = Product.objects.filter(shipment=_shipment_details).select_related('product').\
                        order_by('id')
                    ignored_response, cost = calculate_shipment(_shipment_products, _shipment_details.user.id,
                                                                save_product_price=True)
                    _shipment_details.cost = cost
                    _shipment_details.is_sandbox = is_sandbox
                    _shipment_details.save(update_fields=['cost', 'is_sandbox'])
                    paypal_dict = {
                        'business': paypal_business,
                        'amount': _shipment_details.cost,
                        'item_name': _('Envio %(number)s') % {'number': pid},
                        'invoice': invoice_id,
                        'notify_url': 'https://' + request.CURRENT_DOMAIN + reverse('paypal-ipn'),
                        'return_url': 'https://' + request.CURRENT_DOMAIN + reverse('shipment_details', args=[pid]),
                        'cancel_return': 'https://' + request.CURRENT_DOMAIN + reverse('shipment_details', args=[pid]),
                        # 'custom': 'Custom command!',  # Custom command to correlate to some function later (optional)
                    }
                    paypal_form = MyPayPalSharedSecretEncryptedPaymentsForm(is_sandbox=is_sandbox, initial=paypal_dict,
                                                                            paypal_cert=paypal_cert,
                                                                            cert_id=paypal_cert_id,
                                                                            private_cert=paypal_private_cert,
                                                                            public_cert=paypal_public_cert)
                    rendered_response = paypal_form.render()
                    logger.info(paypal_dict)
                    logger.info(rendered_response)
                    return HttpResponse(rendered_response)
        except Shipment.DoesNotExist as e:
            logger.error(e)
            try:
                error_400_template = loader.get_template('error/400_shipment.html')
            except TemplateDoesNotExist:
                return HttpResponseBadRequest()
            return HttpResponseBadRequest(error_400_template.render())
    return HttpResponseForbidden()


def edit_warehouse(package_formset, pid, save_pdf, ignore_package_fields):
    logger.debug('@@@@@@@@@@@@@@@ EDIT WAREHOUSE @@@@@@@@@@@@@@@@@')
    form_has_changed = False

    if save_pdf:
        if 'weight' not in ignore_package_fields:
            ignore_package_fields.append('weight')
        if 'height' not in ignore_package_fields:
            ignore_package_fields.append('height')
        if 'width' not in ignore_package_fields:
            ignore_package_fields.append('width')
        if 'length' not in ignore_package_fields:
            ignore_package_fields.append('length')
        if 'shipment_tracking' not in ignore_package_fields:
            ignore_package_fields.append('shipment_tracking')
    else:
        if 'pdf_2' not in ignore_package_fields:
            ignore_package_fields.append('pdf_2')
        if 'weight' not in ignore_package_fields:
            ignore_package_fields.append('weight')
        if 'height' not in ignore_package_fields:
            ignore_package_fields.append('height')
        if 'width' not in ignore_package_fields:
            ignore_package_fields.append('width')
        if 'length' not in ignore_package_fields:
            ignore_package_fields.append('length')
        if 'shipment_tracking' not in ignore_package_fields:
            ignore_package_fields.append('shipment_tracking')

    for package_form in package_formset:
        if package_form.has_changed() is False:
            logger.debug('Nothing changed')
            continue
        update_fields_fields = list(
            set(package_form.changed_data).difference(set(ignore_package_fields)))
        if len(update_fields_fields) == 0:
            continue
        form_has_changed = True
        package = package_form.save(commit=False)
        logger.debug(package.shipment.id)
        logger.debug(pid)
        logger.debug(package_form.has_changed())
        if force_text(package.shipment.id) != force_text(pid):
            logger.error('Inconsistent data.')
            raise Shipment.DoesNotExist('Inconsistent data.')
        package.save(update_fields=update_fields_fields)
    return form_has_changed


def shipment_add_status_one_data(request, PackageFormSet, shipment_extra_info, pid=None):
    logger.debug('@@@@@@@@@@@@ ADD PACKAGE @@@@@@@@@@@@@@')
    try:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().select_related('user').get(pk=pid, status=1)
            kwargs = {'addText': _('Adicionar pacote'), 'deleteText': _('Remover pacote'), 'allowEmptyForm': False,
                      'noValidateFields': ['pdf_2'] if shipment.type is None else ['pdf_2', 'warehouse']}
            package_formset = PackageFormSet(request.POST, instance=shipment, prefix='package_set', **kwargs)
            if package_formset.is_valid():
                shipment_products = Product.objects.filter(shipment=shipment)
                session_products = request.session.pop('shipment_products', '[]')
                session_products = json.loads(session_products)
                logger.debug(str(len(shipment_products)))
                logger.debug(str(len(session_products)))
                if len(shipment_products) != len(session_products):
                    raise Product.DoesNotExist('Inconsistent data.')
                shipment.status = 2
                if shipment_extra_info:
                    shipment.information = shipment_extra_info
                    shipment.save(update_fields=['status', 'information'])
                else:
                    shipment.save(update_fields=['status'])
                packages = package_formset.save()
                send_email_shipment_add_package(request, shipment, packages)
                return HttpResponseRedirect('%s?s=1' % reverse('shipment_details', args=[pid]))
            else:
                logger.error(package_formset.errors)
        return package_formset
    except (Product.DoesNotExist, Shipment.DoesNotExist) as err:
        logger.error(err)
        logger.exception(err)
        return HttpResponseBadRequest()


@login_required
@require_http_methods(["DELETE"])
def shipment_delete_product(request, output=None):
    if has_shipment_perm(request.user, 'change_shipment') is False:
        return HttpResponseForbidden()
    request.DELETE = QueryDict(request.body)
    logger.debug('@@@@@@@@@@@@ DELETE PRODUCT @@@@@@@@@@@@@@')
    try:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().select_related('user').\
                get(pk=request.DELETE.get('delete_product_shipment_id'), status=1, is_archived=False, is_canceled=False)
            product = Product.objects.select_for_update().get(pk=request.DELETE.get('delete_product_product_id'),
                                                              shipment=shipment)
            logger.debug(product.quantity)
            shipment.total_products -= product.quantity
            OriginalProduct.objects.filter(pk=product.product_id).update(quantity=F('quantity') + product.quantity,
                                                                         quantity_partial=
                                                                         F('quantity_partial') + product.quantity)
            deleted = product.delete()
            if deleted[0] == 0:
                raise Product.DoesNotExist('Delete did not affect any row.')
            if shipment.total_products == 0:
                redirect_url = resolve_url(shipment)
                shipment.delete()
                return HttpResponse(json.dumps({'redirect': redirect_url}), content_type='application/json')
            products = shipment.product_set.all()
            logger.debug('@@@@@@@@@@@@ SHIPMENT PRODUCTS @@@@@@@@@@@@@@')
            logger.debug(products)
            http_response, cost = calculate_shipment(products, shipment.user.id)
            shipment.cost = cost
            shipment.save(update_fields=['total_products', 'cost'])
    except (Product.DoesNotExist, Shipment.DoesNotExist) as err:
        logger.error(err)
        return HttpResponseBadRequest()
    return http_response


def resolve_url(_shipment_details):
    if _shipment_details.type:
        return reverse('merchant_shipment')
    else:
        return reverse('shipment')


@login_required
@require_http_methods(["GET"])
@transaction.atomic
def shipment_status(request, pid=None, op=None):
    if has_group(request.user, 'admins'):
        shipment = Shipment.objects.select_for_update().filter(pk=pid, is_archived=False, is_canceled=False)
        if shipment:
            if op == 'forward' and shipment[0].status < 4:
                if shipment[0].status == 3:
                    products = shipment[0].product_set.all()
                    ignored_response, cost = calculate_shipment(products, shipment[0].user_id, save_product_price=True)
                    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(shipment[0].user)
                    shipment.update(status=F('status') + 1, cost=cost, is_sandbox=is_sandbox,
                                    payment_date=timezone.now())
                    send_email_shipment_paid(request, shipment[0], async=True)
                else:
                    shipment.update(status=F('status') + 1)
            elif op == 'backward' and shipment[0].status > 1:
                if shipment[0].status == 4:
                    shipment.update(status=F('status') - 1, payment_date=None)
                else:
                    shipment.update(status=F('status') - 1)
    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))


@login_required
@require_http_methods(["POST"])
def shipment_archive(request, pid=None, op='0'):
    redirect_url = None
    try:
        with transaction.atomic():
            if request.POST.get('archive_shipment') is None:
                raise Shipment.DoesNotExist('archive_shipment parameter not found in request.')
            _shipment_details = Shipment.objects.select_for_update().get(pk=pid, is_canceled=False)
            redirect_url = resolve_url(_shipment_details)
            if request.user != _shipment_details.user and has_group(request.user, 'admins') is False:
                raise Shipment.DoesNotExist('Shipment from another user and user is not from admins group.')
            if op == '1':
                if _shipment_details.is_archived is False:
                    raise Shipment.DoesNotExist('Shipment already active.')
                fields_to_update = []
                _shipment_details.is_archived = False
                fields_to_update.append('is_archived')
                if _shipment_details.status == 5:
                    _shipment_details.save(update_fields=fields_to_update)
                    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
                products = _shipment_details.product_set.select_for_update().all()
                for product in products:
                    original_product = OriginalProduct.objects.select_for_update().get(pk=product.product_id)
                    new_quantity_partial = original_product.quantity_partial - product.quantity
                    if new_quantity_partial < 0:
                        if 'total_products' not in fields_to_update:
                            fields_to_update.append('total_products')
                        _shipment_details.total_products -= product.quantity
                        product.quantity += new_quantity_partial
                        if product.quantity < 1:
                            product.delete()
                            continue
                        product.save(update_fields=['quantity'])
                        _shipment_details.total_products += product.quantity
                        new_quantity_partial = 0
                    new_quantity = original_product.quantity - product.quantity
                    OriginalProduct.objects.filter(pk=product.product_id).\
                        update(quantity=new_quantity, quantity_partial=new_quantity_partial)
                if _shipment_details.total_products < 1:
                    _shipment_details.delete()
                    return HttpResponseRedirect('%s?ra=1' % redirect_url)
                if fields_to_update:
                    _shipment_details.save(update_fields=fields_to_update)
                return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
            elif op == '2':
                if _shipment_details.is_archived is True:
                    raise Shipment.DoesNotExist('Shipment already archived.')
                Shipment.objects.filter(pk=pid).update(is_archived=True)
                if _shipment_details.status == 5:
                    return HttpResponseRedirect(redirect_url)
                products = _shipment_details.product_set.select_for_update().all()
                for product in products:
                    OriginalProduct.objects.select_for_update().filter(pk=product.product_id).\
                        update(quantity=F('quantity') + product.quantity,
                               quantity_partial=F('quantity_partial') + product.quantity)
    except Shipment.DoesNotExist as err:
        logger.error(err)
    except OriginalProduct.DoesNotExist as err:
        logger.error(err)
    if redirect_url:
        return HttpResponseRedirect(redirect_url)
    else:
        return HttpResponseRedirect(reverse('product_stock'))


@login_required
@require_http_methods(["POST"])
def shipment_cancel(request, pid=None):
    redirect_url = None
    try:
        with transaction.atomic():
            if request.POST.get('cancel_shipment') is None:
                raise Shipment.DoesNotExist('cancel_shipment parameter not found in request.')
            _shipment_details = Shipment.objects.select_for_update().get(pk=pid)
            redirect_url = resolve_url(_shipment_details)
            if request.user != _shipment_details.user and has_group(request.user, 'admins') is False:
                raise Shipment.DoesNotExist('Shipment from another user and user is not from admins group.')
            cancel_shipment(_shipment_details)
    except Shipment.DoesNotExist as err:
        logger.error(err)
    except OriginalProduct.DoesNotExist as err:
        logger.error(err)
    if redirect_url:
        return HttpResponseRedirect(redirect_url)
    else:
        return HttpResponseRedirect(reverse('product_stock'))


def cancel_shipment(_shipment_details):
    updated_rows = Shipment.objects.filter(pk=_shipment_details.id).update(is_canceled=True)
    if updated_rows == 0:
        raise Shipment.DoesNotExist('Zero rows updated.')
    if _shipment_details.is_archived is False:
        products = _shipment_details.product_set.select_for_update().all()
        for product in products:
            OriginalProduct.objects.select_for_update().filter(pk=product.product_id). \
                update(quantity=F('quantity') + product.quantity,
                       quantity_partial=F('quantity_partial') + product.quantity)


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
    billing = Billing.objects.first()
    if billing:
        billing_type = billing.type
    else:
        billing_type = 2  # por serviço
    ShipmentFormSet = modelformset_factory(Shipment, fields=('pdf_1',), min_num=1, max_num=1,
                                           widgets={'pdf_1': FileInput(attrs={'class': 'form-control pdf_1-validate'})})
    ProductFormSet = inlineformset_factory(Shipment, Product, formset=helper.MyBaseInlineFormSet, fields=('quantity',
                                                                                                          'product'),
                                           field_classes={'product': Field},
                                           widgets={'product': InlineProductWidget},
                                           formfield_callback=my_formfield_callback,
                                           extra=original_products.count())
    WarehouseFormSet = inlineformset_factory(Shipment, Warehouse, formset=helper.MyBaseInlineFormSet,
                                             fields=('name', 'description'), extra=1)
    kwargs_p = {'addText': _('Adicionar produto'), 'deleteText': _('Remover produto')}
    kwargs_w = {'addText': _('Adicionar warehouse'), 'deleteText': _('Remover warehouse')}
    logger.debug('@@@@@@@@@@@@ REQUEST METHOD @@@@@@@@@@@@@@')
    logger.debug(request.method)
    if request.method == 'GET' and request.GET.get('s') == '1':
        return render(request, 'shipment_add.html', {'title': _('Envio'), 'success': True,
                                                     'success_message': _('Envio inserido com sucesso.'),
                                                     'shipment_formset':
                                                         ShipmentFormSet(queryset=Shipment.objects.none()),
                                                     'product_formset':
                                                         ProductFormSet(prefix='product_set', **kwargs_p),
                                                     'warehouse_formset':
                                                         WarehouseFormSet(prefix='warehouse_set', **kwargs_w)})
    logger.debug(str(request.method == 'POST' and request.POST.get('save_shipment')))
    if request.method == 'POST' and request.POST.get('save_shipment'):
        shipment_formset = ShipmentFormSet(request.POST, request.FILES, queryset=Shipment.objects.none())
        product_formset = ProductFormSet(request.POST, prefix='product_set', **kwargs_p)
        warehouse_formset = WarehouseFormSet(request.POST, prefix='warehouse_set', **kwargs_w)
        shipment_formset_is_valid = shipment_formset.is_valid()
        product_formset_is_valid = product_formset.is_valid()
        warehouse_formset_is_valid = warehouse_formset.is_valid()
        if shipment_formset_is_valid and product_formset_is_valid and warehouse_formset_is_valid:
            with transaction.atomic():
                for shipment_form in shipment_formset:
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVE PROCESS @@@@@@@@@@@@@@')
                    shipment = shipment_form.save(commit=False)
                    shipment.user = request.user
                    shipment.status = 1  # Preparing for Shipment
                    shipment.total_products = 0
                    products = product_formset.save(commit=False)
                    for product in products:
                        OriginalProduct.objects.filter(pk=product.product_id).update(quantity=
                                                                                     F('quantity') - product.quantity,
                                                                                     quantity_partial=
                                                                                     F('quantity_partial') -
                                                                                     product.quantity)
                        original_product = OriginalProduct.objects.get(pk=product.product_id)
                        product.receive_date = original_product.receive_date
                        shipment.total_products += product.quantity
                    if billing_type == 2:
                        shipment.cost = 0
                    else:
                        ignored_response, cost = calculate_shipment(products, request.user.id)
                        if cost > 0:
                            shipment.cost = cost
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVE @@@@@@@@@@@@@@')
                    shipment.save()
                    product_formset.instance = shipment
                    warehouse_formset.instance = shipment
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVED @@@@@@@@@@@@@@')
                    product_formset.save()
                    warehouses = warehouse_formset.save()
                    logger.debug('@@@@@@@@@@@@ SEND PDF 1 EMAIL @@@@@@@@@@@@@@')
                    send_email_shipment_add(request, shipment, products, warehouses)
            return HttpResponseRedirect('%s?s=1' % reverse('shipment_add'))
        else:
            logger.warning('@@@@@@@@@@@@ FORM ERRORS @@@@@@@@@@@@@@')
            logger.warning(shipment_formset.errors)
            logger.warning(product_formset.errors)
    else:
        shipment_formset = ShipmentFormSet(queryset=Shipment.objects.none())
        product_formset = ProductFormSet(prefix='product_set', **kwargs_p)
        warehouse_formset = WarehouseFormSet(prefix='warehouse_set', **kwargs_w)
        for subform, data in zip(product_formset.forms, original_products):
            subform.initial = {
                'quantity': data.quantity_partial,
                'product': data
            }
    return render(request, 'shipment_add.html', {'title': _('Envio'), 'shipment_formset': shipment_formset,
                                                 'product_formset': product_formset,
                                                 'warehouse_formset': warehouse_formset,
                                                 'billing_type': billing_type})


@login_required
@require_http_methods(["GET", "POST"])
def merchant_shipment_add(request):
    if has_shipment_perm(request.user, 'add_fbm_shipment') is False:
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
    billing = Billing.objects.first()
    if billing:
        billing_type = billing.type
    else:
        billing_type = 2  # por serviço
    ShipmentFormSet = modelformset_factory(Shipment, fields=('type',), min_num=1, max_num=1)
    ProductFormSet = inlineformset_factory(Shipment, Product, formset=helper.MyBaseInlineFormSet, fields=('quantity',
                                                                                                          'product'),
                                           field_classes={'product': Field},
                                           widgets={'product': InlineProductWidget},
                                           formfield_callback=my_formfield_callback,
                                           extra=original_products.count())
    kwargs_p = {'addText': _('Adicionar produto'), 'deleteText': _('Remover produto')}
    logger.debug('@@@@@@@@@@@@ REQUEST METHOD @@@@@@@@@@@@@@')
    logger.debug(request.method)
    if request.method == 'GET' and request.GET.get('s') == '1':
        return render(request, 'merchant_shipment_add.html', {'title': _('Envio Merchant'), 'success': True,
                                                              'success_message': _('Envio inserido com sucesso.'),
                                                              'shipment_formset':
                                                                  ShipmentFormSet(queryset=Shipment.objects.none()),
                                                              'product_formset':
                                                                  ProductFormSet(prefix='product_set', **kwargs_p)})
    logger.debug(str(request.method == 'POST' and request.POST.get('save_shipment')))
    if request.method == 'POST' and request.POST.get('save_shipment'):
        shipment_formset = ShipmentFormSet(request.POST, request.FILES, queryset=Shipment.objects.none())
        product_formset = ProductFormSet(request.POST, prefix='product_set', **kwargs_p)
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
                        OriginalProduct.objects.filter(pk=product.product_id).update(quantity=
                                                                                     F('quantity') - product.quantity,
                                                                                     quantity_partial=
                                                                                     F('quantity_partial') -
                                                                                     product.quantity)
                        original_product = OriginalProduct.objects.get(pk=product.product_id)
                        product.receive_date = original_product.receive_date
                        shipment.total_products += product.quantity
                    if billing_type == 2:
                        shipment.cost = 0
                    else:
                        ignored_response, cost = calculate_shipment(products, request.user.id)
                        if cost > 0:
                            shipment.cost = cost
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVE @@@@@@@@@@@@@@')
                    shipment.save()
                    product_formset.instance = shipment
                    logger.debug('@@@@@@@@@@@@ SHIPMENT SAVED @@@@@@@@@@@@@@')
                    product_formset.save()
                    send_email_merchant_shipment_add(request, shipment, products)
            return HttpResponseRedirect('%s?s=1' % reverse('merchant_shipment_add'))
        else:
            logger.warning('@@@@@@@@@@@@ FORM ERRORS @@@@@@@@@@@@@@')
            logger.warning(shipment_formset.errors)
            logger.warning(product_formset.errors)
    else:
        shipment_formset = ShipmentFormSet(queryset=Shipment.objects.none())
        product_formset = ProductFormSet(prefix='product_set', **kwargs_p)
        for subform, data in zip(product_formset.forms, original_products):
            subform.initial = {
                'quantity': data.quantity_partial,
                'product': data
            }
    return render(request, 'merchant_shipment_add.html', {'title': _('Envio Merchant'),
                                                          'shipment_formset': shipment_formset,
                                                          'product_formset': product_formset,
                                                          'billing_type': billing_type})


@login_required
@require_http_methods(["GET"])
def shipment_calculate(request):
    if has_shipment_perm(request.user, 'add_shipment') is False and \
                    has_shipment_perm(request.user, 'add_fbm_shipment') is False:
        return HttpResponseForbidden()
    billing = Billing.objects.first()
    if billing:
        billing_type = billing.type
    else:
        billing_type = 2  # por serviço
    if billing_type == 2:
        return HttpResponseBadRequest()
    try:
        items = json.loads(request.GET.get('items'))
    except ValueError as e:
        logger.error(e)
        return HttpResponseBadRequest()
    products = []
    logger.debug('@@@@@@@@@@@@ CALCULATE @@@@@@@@@@@@@@')
    logger.debug(items)
    for item in items:
        logger.debug(item)
        product = Product()
        try:
            product.product = OriginalProduct.objects.get(pk=item['p'], user=request.user)
            product.receive_date = product.product.receive_date
        except OriginalProduct.DoesNotExist as e:
            logger.error(e)
            return HttpResponseBadRequest()
        product.quantity = item['q']
        products.append(product)
    http_response, cost = calculate_shipment(products, request.user.id)
    return http_response


def calculate_shipment(products, user_id, save_product_price=False):
    if len(products) == 0:
        return HttpResponseBadRequest(), 0
    user_model = get_user_model()
    try:
        current_user = user_model.objects.select_related('partner').get(pk=user_id)
        partner = current_user.partner
    except user_model.DoesNotExist:
        return HttpResponseBadRequest(), 0
    cost = 0
    quantity = 0
    billing = Billing.objects.first()
    if billing:
        billing_type = billing.type
    else:
        billing_type = 2  # por serviço
    cost_formula = CostFormula.objects.first()
    if cost_formula:
        for product in products:
            formula = helper.resolve_formula(cost_formula.formula, partner, product,
                                             save_product_price, billing_type)
            logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            logger.debug(formula)
            cost += helper.Calculate().evaluate(formula, variables={'x': product.quantity})
            quantity += product.quantity
    else:
        for product in products:
            cost += product.quantity * (helper.resolve_price_value(product, billing_type) +
                                        helper.resolve_partner_value(partner))
            quantity += product.quantity
    if billing_type == 2:
        config = Config.objects.first()
        if config and cost < config.minimum_price:
            cost = config.minimum_price
    return HttpResponse(json.dumps({'cost': force_text(formats.number_format(round(cost, 2), use_l10n=True,
                                                                             decimal_pos=2)),
                                    'items': quantity}),
                        content_type='application/json'), float(Decimal(round(cost, 2)))


@login_required
@require_http_methods(["GET"])
def shipment_download_pdf(request, pdf=None, pid=None):
    if pdf == 'pdf_1':
        try:
            shipment = Shipment.objects.get(pk=pid)
            pdf_field = shipment.pdf_1
            user = shipment.user
        except Shipment.DoesNotExist as e:
            logger.error(e)
            return HttpResponseBadRequest()
    else:
        try:
            package = Package.objects.get(pk=pid)
            pdf_field = package.pdf_2
            user = package.shipment.user
        except Package.DoesNotExist as e:
            logger.error(e)
            return HttpResponseBadRequest()
    if user == request.user or request.user.groups.filter(name='admins').exists():
        content_type = magic.from_file(os.path.sep.join([settings.MEDIA_ROOT, pdf_field.name]), mime=True)
        filename = pdf_field.name.split('/')[-1]
        logger.debug('@@@@@@@@@@@@ FILE CONTENT TYPE @@@@@@@@@@@@@@')
        logger.debug(filename)
        logger.debug(content_type)
        response = HttpResponse(pdf_field, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
    else:
        return HttpResponseForbidden()


def shipment_paypal_notification(user_id, shipment_id, ipn_obj):
    try:
        _shipment_details = Shipment.objects.select_related('user').get(pk=shipment_id, user_id=user_id)
        if str(_shipment_details.cost) != str(ipn_obj.payment_gross):
            texts = (_('Valor do pagamento não confere com o valor cobrado.'),
                     _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice},
                     _('Valor pago: %(paid)s') % {'paid': ipn_obj.payment_gross},
                     _('Valor cobrado: %(charged)s') % {'charged': _shipment_details.cost})
            return None, texts
    except Shipment.DoesNotExist:
        texts = (_('Dados do recibo são inválidos.'), _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice})
        return None, texts
    return _shipment_details, None


def shipment_paypal_notification_success(request, _shipment_details, ipn_obj, paypal_status_message):
    _shipment_details.payment_date = timezone.now()
    updated_rows = Shipment.objects.filter(pk=_shipment_details.id, status=3)\
        .update(status=4, payment_date=_shipment_details.payment_date)
    if updated_rows == 0:
        logger.error('Zero rows updated.')
        raise helper.PaymentException()
    email_title = _('Pagamento confirmado pelo PayPal para o %(item)s') % {'item': ipn_obj.item_name}
    email_message = paypal_status_message
    helper.send_email_basic_template_bcc_admins(request, _shipment_details.user.first_name,
                                                [_shipment_details.user.email], email_title, email_message, async=True)
    send_email_shipment_paid(request, _shipment_details, async=True)


def send_email_shipment_add(request, shipment, products, warehouses):
    email_title = _('Cadastro de Envio %(number)s') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> {}</p>'] * 2 +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong>'
                           '<br> {} {}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> {}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> U$ {}</p>'] +
                          ['<br>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">'
                           '<strong>{}:</strong> {}</p>'] * len(warehouses) +
                          ['<br>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">'
                           '<strong>{}:</strong> {}</p>'
                           '<p style="color:#858585;font:13px/120%% \'Helvetica\'">'
                           '<strong>{}:</strong> {}</p>{}'] * len(products) +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Seu envio foi cadastrado com sucesso. Seguem abaixo os dados do envio:'),
             _('Envio'), shipment.id,
             _('Data de criação'),
             # force_text(formats.localize(shipment.send_date, use_l10n=True)),
             formats.date_format(helper.localize_date(shipment.created_date), "SHORT_DATE_FORMAT"),
             _('Previsão de cadastro do(s) pacote(s)'),
             formats.date_format(etc(shipment.created_date, estimate='preparation'), "SHORT_DATE_FORMAT"),
             _('inclusive'),
             _('Quantidade de produtos'), shipment.total_products,
             _('Valor total'), force_text(formats.number_format(shipment.cost, use_l10n=True, decimal_pos=2)),)

    for warehouse in warehouses:
        texts += (_('Warehouse'), warehouse.name)
    for product in products:
        texts += (_('Produto'), product.product.name, _('Quantidade'), product.quantity)
        if product.product.best_before:
            texts += (mark_safe('<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>%(best_before_label)s:'
                                '</strong> %(best_before_value)s</p>'
                                % {'best_before_label': _('Validade'),
                                   'best_before_value': formats.date_format(product.product.best_before,
                                                                            "SHORT_DATE_FORMAT")}),)
        else:
            texts += ('',)
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment')]), _('Clique aqui'),
              _('para acessar sua lista de envios.'))
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=True)


def send_email_merchant_shipment_add(request, shipment, products):
    email_title = _('Cadastro de Envio Merchant %(number)s') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> {}</p>'] * 2 +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong>'
                           '<br> {} {}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> {}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> U$ {}</p>'] +
                          ['<br>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">'
                           '<strong>{}:</strong> {}</p>'
                           '<p style="color:#858585;font:13px/120%% \'Helvetica\'">'
                           '<strong>{}:</strong> {}</p>{}'] * len(products) +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Seu envio foi cadastrado com sucesso. Seguem abaixo os dados do envio:'),
             _('Envio'), shipment.id,
             _('Data de criação'),
             # force_text(formats.localize(shipment.send_date, use_l10n=True)),
             formats.date_format(helper.localize_date(shipment.created_date), "SHORT_DATE_FORMAT"),
             _('Previsão de cadastro do(s) pacote(s)'),
             formats.date_format(etc(shipment.created_date, estimate='preparation'), "SHORT_DATE_FORMAT"),
             _('inclusive'),
             _('Quantidade de produtos'), shipment.total_products,
             _('Valor total'), force_text(formats.number_format(shipment.cost, use_l10n=True, decimal_pos=2)),)

    for product in products:
        texts += (_('Produto'), product.product.name, _('Quantidade'), product.quantity)
        if product.product.best_before:
            texts += (mark_safe('<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>%(best_before_label)s:'
                                '</strong> %(best_before_value)s</p>'
                                % {'best_before_label': _('Validade'),
                                   'best_before_value': formats.date_format(product.product.best_before,
                                                                            "SHORT_DATE_FORMAT")}),)
        else:
            texts += ('',)
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('merchant_shipment')]), _('Clique aqui'),
              _('para acessar sua lista de envios merchant.'))
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=True)


def send_email_shipment_add_package(request, shipment, packages, async=True):
    email_title = _('Notificação de mudança de status do Envio %(number)s') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">Warehouse: {} / {}: {} {} / '
                           'L: {}{} x W: {}{} x H: {}{}</p>'] * len(packages) +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}</strong></p>',
                           '<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Os seguintes pacotes foram cadastrado para o seu envio:'),)
    for package in packages:
        texts += (package.warehouse, _('Peso'), package.weight, unit_weight_display(1, abbreviate=True), package.length,
                  unit_length_display(3, abbreviate=True), package.width, unit_length_display(3, abbreviate=True),
                  package.height, unit_length_display(3, abbreviate=True))
    texts += (ungettext('Agora faça o upload da etiqueta da caixa para dar continuidade com o seu envio '
                        '%(id)s.', 'Agora faça o upload das etiquetas das caixas para dar continuidade com o '
                                   'seu envio %(id)s.', len(packages)) % {'id': shipment.id},
              ''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment_details', args=[shipment.id])]),
              _('Clique aqui'), _('para acessar seu envio e efetuar o upload.'),)
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async)


def send_email_shipment_payment(request, shipment):
    texts = (_('Obrigado, agora realize o pagamento para dar continuidade com o seu '
               'envio %(id)s.') % {'id': shipment.id}, _('Valor total'),
             force_text(formats.number_format(shipment.cost, use_l10n=True, decimal_pos=2)),)
    send_email_shipment_status_change(request, shipment, _('para acessar seu envio e efetuar o pagamento.'), *texts,
                                      async=True)


def send_email_shipment_paid(request, shipment, async=False):
    texts = (_('Obrigado novamente, agora é só aguardar que, assim que fizermos as checagens finais e tudo estiver ok, '
               'iremos enviar um novo e-mail para avisar da conclusão do processo do seu envio %(id)s.')
             % {'id': shipment.id}, _('Previsão para conclusão'),
             formats.date_format(etc(shipment.payment_date, estimate='shipment'), "SHORT_DATE_FORMAT"),
             _('inclusive'),)
    send_email_shipment_status_change(request, shipment, _('para acessar seu envio.'), *texts, async=async)


def send_email_shipment_sent(request, shipment, packages):
    packages_qty = len(packages)
    email_title = _('Seu envio %(number)s foi concluído') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] if packages_qty > 0
                           else []) +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] * packages_qty +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = [_('Seu envio %(id)s foi concluído com sucesso, obrigado.') % {'id': shipment.id}]
    if packages_qty > 0:
        texts += [ungettext('Segue o código de postagem do seu envio:',
                            'Seguem os códigos de postagem do seu envio:',
                            packages_qty)]
        for package in packages:
            texts += [mark_safe(_('Warehouse: <strong>%(warehouse)s</strong> / Código: <strong>%(code)s</strong>.')
                                % {'warehouse': package.warehouse, 'code': package.shipment_tracking})]
    texts += [mark_safe(_('No caso de qualquer dúvida é só nos enviar uma mensagem através do '
                          '<a href="%(url)s">fale conosco</a>.')
                        % {'url': ''.join(['https://', request.CURRENT_DOMAIN, '/#contact'])})]
    texts += [''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment_details', args=[shipment.id])]),
              _('Clique aqui'), _('para acessar seu envio.')]
    email_body = format_html(html_format, *tuple(texts))
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=True)


def send_email_shipment_change_shipment(request, shipment, packages):
    packages_qty = len(packages)
    email_title = _('Código de postagem do envio %(number)s atualizado') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] * packages_qty +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (ungettext('Segue o código de postagem do seu envio:', 'Seguem os códigos de postagem do seu envio:',
                       packages_qty),)
    for package in packages:
        texts += (mark_safe(_('Warehouse: <strong>%(warehouse)s</strong> / Código: <strong>%(code)s</strong>.')
                            % {'warehouse': package.warehouse, 'code': package.shipment_tracking}),)
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment_details', args=[shipment.id])]),
              _('Clique aqui'), _('para acessar seu envio.'))
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=True)


def send_email_shipment_status_change(request, shipment, link_text, *texts, async=False):
    email_title = _('Notificação de mudança de status do Envio %(number)s') % {'number': shipment.id}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          (['<p style="color:#858585;font:13px/120% \'Helvetica\'">'
                           '<strong>{}:</strong> U$ {}</p>'] if len(texts) == 3 else ['']) +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong>'
                           '<br> {} {}</p>'] if len(texts) == 4 else ['']) +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment_details', args=[shipment.id])]),
              _('Clique aqui'), link_text,)
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=async)
