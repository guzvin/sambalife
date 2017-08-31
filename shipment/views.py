from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from shipment.templatetags.shipments import has_shipment_perm
from myauth.templatetags.users import has_user_perm
from myauth.templatetags.permissions import has_group
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import ugettext as _, ungettext
from product.models import Product as OriginalProduct
from shipment.models import Shipment, Product, Warehouse, Package, CostFormula
from django.forms import modelformset_factory, inlineformset_factory, Field, DateField
from django.forms.widgets import Widget, FileInput
from django.utils.html import format_html, mark_safe
from django.forms.utils import flatatt
from django.db import transaction
from django.utils import formats
from django.utils.encoding import force_text
from django.conf import settings
from django.urls import reverse
from utils import helper
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from payment.forms import MyPayPalSharedSecretEncryptedPaymentsForm
from shipment.templatetags.shipments import unit_weight_display, unit_length_display
from django.contrib.auth import get_user_model
from django.template import loader, TemplateDoesNotExist
from django.utils import translation
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
        filter_archived = request.GET.get('archived')
        logger.debug(str(filter_archived))
        filter_canceled = request.GET.get('canceled')
        logger.debug(str(filter_canceled))
        filter_values = {
            'status': '',
        }
        filter_send_date = request.GET.get('date')
        logger.debug(str(filter_send_date))
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
        if filter_send_date:
            queries.append(Q(send_date=DateField().to_python(filter_send_date)))
            filter_values['date'] = filter_send_date
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
    context_data = {'title': _('Estoque'), 'shipments': shipments, 'filter_values': helper.ObjectView(filter_values)}
    if request.GET.get('ra') == '1':
        context_data['custom_modal'] = True
        context_data['modal_title'] = _('Mensagem importante!')
        context_data['modal_message'] = _('O envio foi removido, pois seus produtos não estavam mais disponíveis em '
                                            'estoque.')
    return render(request, 'shipment_list.html', context_data)


@login_required
@require_http_methods(["GET", "POST"])
def shipment_details(request, pid=None):
    logger.debug('@@@@@@@@@@@@@@@ REMOTE ADDRESS @@@@@@@@@@@@@@@@@')
    logger.debug(request.META)
    if has_shipment_perm(request.user, 'view_shipments'):
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
        _shipment_products = Product.objects.filter(shipment=_shipment_details).select_related('product').order_by('id')
        ignored_response, cost = calculate_shipment(_shipment_products, _shipment_details.user.id)
        _shipment_details.cost = cost
        _shipment_warehouses = Warehouse.objects.filter(shipment=_shipment_details).order_by('id')
        title = ' '.join([str(_('Envio')), str(_shipment_details.id)])
        context_data = {'title': title, 'shipment': _shipment_details, 'products': _shipment_products,
                        'warehouses': _shipment_warehouses}
        custom_error_messages = {'required': _('Campo obrigatório.'), 'invalid': _('Informe um número maior que zero.')}
        PackageFormSet = inlineformset_factory(Shipment, Package, formset=helper.MyBaseInlineFormSet,
                                               fields=('warehouse', 'weight', 'height', 'width', 'length', 'pdf_2',
                                                       'shipment_tracking'),
                                               extra=render_extra_package(_shipment_details),
                                               error_messages={'weight': custom_error_messages,
                                                               'height': custom_error_messages,
                                                               'width': custom_error_messages,
                                                               'length': custom_error_messages},
                                               widgets={'pdf_2': FileInput(
                                                   attrs={'class': 'form-control pdf_2-validate'})})
        package_formset = None
        if _shipment_details.is_archived is False and _shipment_details.is_canceled is False and \
                _shipment_details.status == 1:
            # Preparando para Envio
            if request.method == 'POST' and request.POST.get('add_shipment_package'):
                if has_shipment_perm(request.user, 'add_package'):
                    package_formset = shipment_add_package(request, PackageFormSet, pid)
                    if isinstance(package_formset, HttpResponse):
                        return package_formset
                    context_data['packages'] = package_formset
                else:
                    return HttpResponseForbidden()
            if has_shipment_perm(request.user, 'add_package'):
                serialized_products = serializers.serialize('json', _shipment_products, fields=('id', 'quantity',
                                                                                                'product',))
                logger.debug('@@@@@@@@@@@@@@@ SERIALIZED PRODUCTS @@@@@@@@@@@@@@@@@')
                logger.debug(serialized_products)
                request.session['shipment_products'] = serialized_products
        elif _shipment_details.is_archived is False and _shipment_details.is_canceled is False:
            PackageFormSet.extra = 0
            PackageFormSet.max_num = 1
            novalidate_fields = []
            if _shipment_details.status != 2:
                novalidate_fields.append('pdf_2')
            package_kwargs = {'renderEmptyForm': False, 'noValidateFields': novalidate_fields}
            if _shipment_details.status == 3:
                # Pagamento Autorizado
                if request.user == _shipment_details.user or has_group(request.user, 'admins') \
                        or has_shipment_perm(request.user, 'add_package'):
                    if request.method == 'GET':
                        if request.GET.get('s') == '1':
                            package_formset = PackageFormSet(
                                queryset=Package.objects.filter(shipment=_shipment_details).order_by('id'),
                                instance=_shipment_details, prefix='package_set', **package_kwargs)
                            context_data['success'] = True
                            context_data['success_message'] = ungettext('Upload realizado com sucesso.',
                                                                        'Uploads realizados com sucesso.',
                                                                        len(package_formset))
                        elif request.GET.get('s') == '2':
                            context_data['success'] = True
                            context_data['success_message'] = _('Alteração salva com sucesso.')
                    elif request.method == 'POST' and has_shipment_perm(request.user, 'add_package'):
                        package_formset = PackageFormSet(request.POST, instance=_shipment_details, prefix='package_set',
                                                         **package_kwargs)
                        if package_formset.is_valid():
                            try:
                                if edit_warehouse(package_formset, pid):
                                    return HttpResponseRedirect('%s?s=2' % reverse('shipment_details', args=[pid]))
                                else:
                                    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
                            except Shipment.DoesNotExist as e:
                                logger.error(e)
                                return HttpResponseBadRequest()
                if request.user == _shipment_details.user or has_group(request.user, 'admins'):
                    is_sandbox = paypal_mode(request)
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
                        elif request.GET.get('s') == '2':
                            context_data['success'] = True
                            context_data['success_message'] = _('Alteração salva com sucesso.')
                    elif request.method == 'POST' and request.POST.get('add_package_file'):
                        package_formset = PackageFormSet(request.POST, request.FILES, instance=_shipment_details,
                                                         prefix='package_set', **package_kwargs)
                        logger.debug('@@@@@@@@@@@@@@@ PDF 2 IS VALID @@@@@@@@@@@@@@@@@')
                        logger.debug(package_formset)
                        if package_formset.is_valid() and (request.user == _shipment_details.user
                                                           or has_group(request.user, 'admins')):
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
                                        if has_group(request.user, 'admins'):
                                            package.save(update_fields=['warehouse', 'pdf_2'])
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
                                if edit_warehouse(package_formset, pid):
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
                        elif has_shipment_perm(request.user, 'add_package') and request.GET.get('s') == '2':
                            context_data['success'] = True
                            context_data['success_message'] = _('Código(s) de postagem salvo(s) com sucesso.')
                if has_group(request.user, 'admins') or has_shipment_perm(request.user, 'add_package'):
                    if request.method == 'POST' and request.POST.get('add_package_tracking'):
                        package_formset = PackageFormSet(request.POST, instance=_shipment_details, prefix='package_set',
                                                         **package_kwargs)
                        if package_formset.is_valid():
                            try:
                                with transaction.atomic():
                                    form_has_changed = False
                                    packages = []
                                    for package_form in package_formset:
                                        if package_form.has_changed() is False:
                                            continue
                                        form_has_changed = True
                                        package = package_form.save(commit=False)
                                        package_shipment_id = package.shipment.id
                                        logger.debug(package_shipment_id)
                                        logger.debug(pid)
                                        logger.debug(package_form.has_changed())
                                        if force_text(package_shipment_id) != force_text(pid):
                                            logger.error('Inconsistent data.')
                                            raise Shipment.DoesNotExist('Inconsistent data.')
                                        package.save(update_fields=['shipment_tracking'])
                                        packages.append(package)
                                    previous_state = _shipment_details.status
                                    if _shipment_details.status == 4 and has_group(request.user, 'admins'):
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
        logger.debug(context_data)
        return render(request, 'shipment_details.html', context_data)
    return HttpResponseForbidden()


def paypal_mode(request):
    is_sandbox = (request.user.email in settings.PAYPAL_SANDBOX_USERS) or translation.get_language() == 'en-us'
    return is_sandbox


def complete_shipment(_shipment_details):
    original_products_to_update = []
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
                original_products_to_update.append(product.product_id)
        except OriginalProduct.DoesNotExist:
            pass
    if original_products_to_update:
        OriginalProduct.objects.filter(id__in=original_products_to_update).update(status=99)


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
    if has_shipment_perm(request.user, 'view_shipments'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        query = Q(pk=pid) & Q(status=3) & Q(is_archived=False) & Q(is_canceled=False)
        try:
            with transaction.atomic():
                if is_user_perm is False:
                    query &= Q(user=request.user)
                _shipment_details = Shipment.objects.select_for_update().select_related('user').get(query)
                _shipment_products = Product.objects.filter(shipment=_shipment_details).select_related('product').\
                    order_by('id')
                ignored_response, cost = calculate_shipment(_shipment_products, _shipment_details.user.id,
                                                            save_product_price=True)
                _shipment_details.cost = cost
                if request.user == _shipment_details.user or has_group(request.user, 'admins'):
                    is_sandbox = paypal_mode(request)
                    if settings.PAYPAL_TEST or is_sandbox:
                        invoice_id = '_'.join(['A', str(request.user.id), str(pid), 'debug', str(current_milli_time())])
                        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX if \
                            _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_BUSINESS_EN_SANDBOX
                        paypal_cert_id = settings.PAYPAL_CERT_ID_SANDBOX if \
                            _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_CERT_ID_EN_SANDBOX
                        paypal_cert = settings.PAYPAL_CERT_SANDBOX
                    else:
                        invoice_id = '_'.join(['A', str(request.user.id), str(pid)])
                        paypal_business = settings.PAYPAL_BUSINESS if \
                            _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_BUSINESS_EN
                        paypal_cert_id = settings.PAYPAL_CERT_ID if \
                            _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_CERT_ID_EN
                        paypal_cert = settings.PAYPAL_CERT
                    paypal_private_cert = settings.PAYPAL_PRIVATE_CERT if \
                        _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_PRIVATE_CERT_EN
                    paypal_public_cert = settings.PAYPAL_PUBLIC_CERT if \
                        _shipment_details.user.language_code == 'pt-br' else settings.PAYPAL_PUBLIC_CERT_EN
                    _shipment_details.save(update_fields=['cost'])
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
                    return HttpResponse(paypal_form.render())
        except Shipment.DoesNotExist as e:
            logger.error(e)
            try:
                error_400_template = loader.get_template('error/400_shipment.html')
            except TemplateDoesNotExist:
                return HttpResponseBadRequest()
            return HttpResponseBadRequest(error_400_template.render())
    return HttpResponseForbidden()


def edit_warehouse(package_formset, pid):
    logger.debug('@@@@@@@@@@@@@@@ EDIT WAREHOUSE @@@@@@@@@@@@@@@@@')
    form_has_changed = False
    for package_form in package_formset:
        if package_form.has_changed() is False:
            logger.debug('Nothing changed')
            continue
        form_has_changed = True
        package = package_form.save(commit=False)
        logger.debug(package.shipment.id)
        logger.debug(pid)
        logger.debug(package_form.has_changed())
        if force_text(package.shipment.id) != force_text(pid):
            logger.error('Inconsistent data.')
            raise Shipment.DoesNotExist('Inconsistent data.')
        package.save(update_fields=['warehouse'])
    return form_has_changed


def shipment_add_package(request, PackageFormSet, pid=None):
    if has_shipment_perm(request.user, 'view_shipments') is False or \
                    has_shipment_perm(request.user, 'add_package') is False:
        return HttpResponseForbidden()
    logger.debug('@@@@@@@@@@@@ ADD PACKAGE @@@@@@@@@@@@@@')
    kwargs = {'addText': _('Adicionar pacote'), 'deleteText': _('Remover pacote'), 'allowEmptyForm': False,
              'noValidateFields': ['pdf_2']}
    try:
        with transaction.atomic():
            shipment = Shipment.objects.select_for_update().select_related('user').get(pk=pid, status=1)
            package_formset = PackageFormSet(request.POST, instance=shipment, prefix='package_set', **kwargs)
            if package_formset.is_valid():
                shipment.status = 2
                shipment_products = Product.objects.filter(shipment=shipment)
                session_products = request.session.pop('shipment_products', '[]')
                session_products = json.loads(session_products)
                logger.debug(str(len(shipment_products)))
                logger.debug(str(len(session_products)))
                if len(shipment_products) != len(session_products):
                    raise Product.DoesNotExist('Inconsistent data.')
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
                shipment.delete()
                return HttpResponse(json.dumps({'redirect': reverse('shipment')}), content_type='application/json')
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
                    shipment.update(status=F('status') + 1, cost=cost)
                else:
                    shipment.update(status=F('status') + 1)
            elif op == 'backward' and shipment[0].status > 1:
                shipment.update(status=F('status') - 1)
    return HttpResponseRedirect(reverse('shipment_details', args=[pid]))


@login_required
@require_http_methods(["POST"])
def shipment_archive(request, pid=None, op='0'):
    try:
        with transaction.atomic():
            if request.POST.get('archive_shipment') is None:
                raise Shipment.DoesNotExist('archive_shipment parameter not found in request.')
            _shipment_details = Shipment.objects.select_for_update().get(pk=pid, is_canceled=False)
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
                    return HttpResponseRedirect('%s?ra=1' % reverse('shipment'))
                if fields_to_update:
                    _shipment_details.save(update_fields=fields_to_update)
                return HttpResponseRedirect(reverse('shipment_details', args=[pid]))
            elif op == '2':
                if _shipment_details.is_archived is True:
                    raise Shipment.DoesNotExist('Shipment already archived.')
                Shipment.objects.filter(pk=pid).update(is_archived=True)
                if _shipment_details.status == 5:
                    return HttpResponseRedirect(reverse('shipment'))
                products = _shipment_details.product_set.select_for_update().all()
                for product in products:
                    OriginalProduct.objects.select_for_update().filter(pk=product.product_id).\
                        update(quantity=F('quantity') + product.quantity,
                               quantity_partial=F('quantity_partial') + product.quantity)
    except Shipment.DoesNotExist as err:
        logger.error(err)
    except OriginalProduct.DoesNotExist as err:
        logger.error(err)
    return HttpResponseRedirect(reverse('shipment'))


@login_required
@require_http_methods(["POST"])
def shipment_cancel(request, pid=None):
    try:
        with transaction.atomic():
            if request.POST.get('cancel_shipment') is None:
                raise Shipment.DoesNotExist('cancel_shipment parameter not found in request.')
            _shipment_details = Shipment.objects.select_for_update().get(pk=pid)
            if request.user != _shipment_details.user and has_group(request.user, 'admins') is False:
                raise Shipment.DoesNotExist('Shipment from another user and user is not from admins group.')
            cancel_shipment(_shipment_details)
    except Shipment.DoesNotExist as err:
        logger.error(err)
    except OriginalProduct.DoesNotExist as err:
        logger.error(err)
    return HttpResponseRedirect(reverse('shipment'))


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
    ShipmentFormSet = modelformset_factory(Shipment, fields=('send_date', 'pdf_1',),
                                           localized_fields=('send_date',), min_num=1, max_num=1,
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
                                                 'warehouse_formset': warehouse_formset})


@login_required
@require_http_methods(["GET"])
def shipment_calculate(request):
    if has_shipment_perm(request.user, 'add_shipment') is False:
        return HttpResponseForbidden()
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
    try:
        cost_formula = CostFormula.objects.first()
        for product in products:
            formula = helper.resolve_formula(cost_formula.formula, current_user.language_code, partner, product,
                                             save_product_price)
            logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            logger.debug(formula)
            cost += helper.Calculate().evaluate(formula, variables={'x': product.quantity})
            quantity += product.quantity
    except CostFormula.DoesNotExist:
        for product in products:
            cost += product.quantity * (helper.resolve_price_value(product.receive_date, current_user.language_code) +
                                        helper.resolve_partner_value(partner))
            quantity += product.quantity
    return HttpResponse(json.dumps({'cost': force_text(formats.localize(round(cost, 2), use_l10n=True)),
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
    updated_rows = Shipment.objects.filter(pk=_shipment_details.id, status=3).update(status=4)
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
                          ['<p style="color:#858585;font:13px/120%% \'Helvetica\'"><strong>{}:</strong> {}</p>'] * 3 +
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
             _('Data de envio'), force_text(formats.localize(shipment.send_date, use_l10n=True)),
             _('Quantidade de produtos'), shipment.total_products,
             _('Valor total'), force_text(formats.localize(shipment.cost, use_l10n=True)),)

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
             force_text(formats.localize(shipment.cost, use_l10n=True)),)
    send_email_shipment_status_change(request, shipment, _('para acessar seu envio e efetuar o pagamento.'), *texts,
                                      async=True)


def send_email_shipment_paid(request, shipment, async=False):
    texts = (_('Obrigado novamente, agora é só aguardar que, assim que fizermos as checagens finais e tudo estiver ok, '
               'iremos enviar um novo e-mail para avisar da conclusão do processo do seu envio %(id)s.')
             % {'id': shipment.id},)
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
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('shipment_details', args=[shipment.id])]),
              _('Clique aqui'), link_text,)
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, shipment.user.first_name, [shipment.user.email], email_title,
                                                email_body, async=async)
