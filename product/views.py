from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.db import transaction
from product.models import Product, Tracking
from shipment.models import Product as ShipmentProduct
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden
from django.utils import formats, timezone
from django.forms import modelformset_factory, inlineformset_factory
from django.urls import reverse
from utils.helper import MyBaseInlineFormSet, ObjectView, send_email_basic_template_bcc_admins, get_max_time_period
from store.models import Collaborator
from product.templatetags.products import has_product_perm
from myauth.templatetags.users import has_user_perm
from store.templatetags.lots import has_store_perm
from django.utils.html import format_html, mark_safe
from django.conf import settings
from django.utils import translation
import json
import logging
import datetime
import pytz

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
def product_stock(request):
    if has_product_perm(request.user, 'view_products'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        is_collaborator_perm = has_store_perm(request.user, 'collaborator')
        queries = []
        logger.debug('@@@@@@@@@@@@ PRODUCT STOCK FILTERS @@@@@@@@@@@@@@')
        logger.debug(settings.DEBUG)
        logger.debug(settings.PAYPAL_TEST)
        filter_collaborator = request.GET.get('collaborator')
        logger.debug(str(filter_collaborator))
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_name = request.GET.get('name')
        logger.debug(str(filter_name))
        filter_asin = request.GET.get('asin')
        logger.debug(str(filter_asin))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_tracking = request.GET.get('tracking')
        logger.debug(str(filter_tracking))
        filter_store = request.GET.get('store')
        logger.debug(str(filter_store))
        filter_archived = request.GET.get('archived')
        logger.debug(str(filter_archived))
        filter_values = {
            'status': '',
        }
        if filter_collaborator is None:
            filter_collaborator = request.user.collaborator
        else:
            try:
                int(filter_collaborator)
                selected_collaborator = Collaborator.objects.get(pk=filter_collaborator)
                filter_collaborator = selected_collaborator
            except (ValueError, TypeError, Collaborator.DoesNotExist):
                filter_collaborator = None
        queries.append(Q(collaborator=filter_collaborator))
        filter_values['collaborator'] = filter_collaborator
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if filter_name:
            queries.append(Q(name__icontains=filter_name))
            filter_values['name'] = filter_name
        if filter_asin:
            queries.append(Q(asin=filter_asin))
            filter_values['asin'] = filter_asin
        if (is_user_perm or is_collaborator_perm) and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user) |
                           Q(user__email__icontains=filter_user) | Q(user__from_key__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        if filter_tracking:
            queries.append(Q(tracking__track_number=filter_tracking))
            filter_values['tracking'] = filter_tracking
        if filter_store:
            queries.append(Q(store__icontains=filter_store))
            filter_values['store'] = filter_store
        if filter_archived and filter_archived == 'on':
            filter_values['archived'] = 'checked=checked'
        else:
            queries.append(~Q(status=99))
        logger.debug('@@@@@@@@@@@@ QUERIES @@@@@@@@@@@@@@')
        logger.debug(str(queries))
        logger.debug(str(len(queries)))
        if is_collaborator_perm and request.user.collaborator:
            queries.append((Q(user=request.user) | Q(collaborator=request.user.collaborator)))
        elif is_user_perm is False:
            queries.append(~Q(status=100))
            queries.append(Q(user=request.user))
        queries.append(Q(stock_type=1))
        is_filtered = len(queries) > 0
        if is_filtered:
            query = queries.pop()
            for item in queries:
                query &= item
            logger.debug(str(query))
        if is_user_perm or (is_collaborator_perm and request.user.collaborator):
            if is_filtered:
                logger.debug('@@@@@@@@@@@@ FILTERED @@@@@@@@@@@@@@')
                products_list = Product.objects.filter(query).select_related('user').order_by('id')
            else:
                logger.debug('@@@@@@@@@@@@ ALL @@@@@@@@@@@@@@')
                products_list = Product.objects.all().select_related('user').order_by('id')
        else:
            products_list = Product.objects.filter(query).order_by('id')
    else:
        products_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(products_list, 30)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    max_time_period = get_max_time_period()
    context_data = {'title': _('Estoque FBA'), 'products': products, 'filter_values': ObjectView(filter_values),
                    'max_time_period': max_time_period if max_time_period else 0,
                    'collaborators': Collaborator.objects.all().order_by('name')}
    user_model = get_user_model()
    UserFormSet = modelformset_factory(user_model, fields=('amz_store_name',), min_num=1, max_num=1)
    user_formset = UserFormSet(queryset=user_model.objects.filter(pk=request.user.pk))
    context_data['user_formset'] = user_formset
    if request.GET.get('s') == '1':
        context_data['custom_modal'] = True
        context_data['modal_title'] = _('We create your AZ Shipment')
        context_data['modal_message'] = _('Envio NÃO criado. Por favor, verifique seu estoque, nenhum produto '
                                          'disponível para envio.')
    return render(request, 'product_stock.html', context_data)


@login_required
@require_http_methods(["GET"])
def product_stock_fbm(request):
    if has_product_perm(request.user, 'view_products'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        is_collaborator_perm = has_store_perm(request.user, 'collaborator')
        queries = []
        logger.debug('@@@@@@@@@@@@ PRODUCT STOCK FILTERS @@@@@@@@@@@@@@')
        logger.debug(settings.DEBUG)
        logger.debug(settings.PAYPAL_TEST)
        filter_collaborator = request.GET.get('collaborator')
        logger.debug(str(filter_collaborator))
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_name = request.GET.get('name')
        logger.debug(str(filter_name))
        filter_asin = request.GET.get('asin')
        logger.debug(str(filter_asin))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_tracking = request.GET.get('tracking')
        logger.debug(str(filter_tracking))
        filter_store = request.GET.get('store')
        logger.debug(str(filter_store))
        filter_archived = request.GET.get('archived')
        logger.debug(str(filter_archived))
        filter_values = {
            'status': '',
        }
        if filter_collaborator is None:
            filter_collaborator = request.user.collaborator
        else:
            try:
                int(filter_collaborator)
                selected_collaborator = Collaborator.objects.get(pk=filter_collaborator)
                filter_collaborator = selected_collaborator
            except (ValueError, TypeError, Collaborator.DoesNotExist):
                filter_collaborator = None
        queries.append(Q(collaborator=filter_collaborator))
        filter_values['collaborator'] = filter_collaborator
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if filter_name:
            queries.append(Q(name__icontains=filter_name))
            filter_values['name'] = filter_name
        if filter_asin:
            queries.append(Q(asin=filter_asin))
            filter_values['asin'] = filter_asin
        if (is_user_perm or is_collaborator_perm) and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user) |
                           Q(user__email__icontains=filter_user) | Q(user__from_key__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        if filter_tracking:
            queries.append(Q(tracking__track_number=filter_tracking))
            filter_values['tracking'] = filter_tracking
        if filter_store:
            queries.append(Q(store__icontains=filter_store))
            filter_values['store'] = filter_store
        if filter_archived and filter_archived == 'on':
            filter_values['archived'] = 'checked=checked'
        else:
            queries.append(~Q(status=99))
        logger.debug('@@@@@@@@@@@@ QUERIES @@@@@@@@@@@@@@')
        logger.debug(str(queries))
        logger.debug(str(len(queries)))
        if is_collaborator_perm and request.user.collaborator:
            queries.append((Q(user=request.user) | Q(collaborator=request.user.collaborator)))
        elif is_user_perm is False:
            queries.append(~Q(status=100))
            queries.append(Q(user=request.user))
        queries.append(Q(stock_type=2))
        is_filtered = len(queries) > 0
        if is_filtered:
            query = queries.pop()
            for item in queries:
                query &= item
            logger.debug(str(query))
        if is_user_perm or (is_collaborator_perm and request.user.collaborator):
            if is_filtered:
                logger.debug('@@@@@@@@@@@@ FILTERED @@@@@@@@@@@@@@')
                products_list = Product.objects.filter(query).select_related('user').order_by('id')
            else:
                logger.debug('@@@@@@@@@@@@ ALL @@@@@@@@@@@@@@')
                products_list = Product.objects.all().select_related('user').order_by('id')
        else:
            products_list = Product.objects.filter(query).order_by('id')
    else:
        products_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(products_list, 30)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    max_time_period = get_max_time_period()
    context_data = {'title': _('Estoque FBM'), 'products': products, 'filter_values': ObjectView(filter_values),
                    'max_time_period': max_time_period if max_time_period else 0,
                    'collaborators': Collaborator.objects.all().order_by('name')}
    if request.GET.get('s') == '1':
        context_data['custom_modal'] = True
        context_data['modal_title'] = _('Envio Merchant')
        context_data['modal_message'] = _('Envio NÃO criado. Por favor, verifique seu estoque, nenhum produto '
                                          'disponível para envio.')
    return render(request, 'product_stock_fbm.html', context_data)


@login_required
@require_http_methods(["GET", "POST"])
def product_add_edit(request, pid=None):
    if 'impersonated' not in request.session:
        if pid is None and has_product_perm(request.user, 'add_product') is False:
            return HttpResponseForbidden()
        elif pid is not None and has_product_perm(request.user, 'change_product') is False:
            return HttpResponseForbidden()
    ProductFormSet = modelformset_factory(Product, fields=('name', 'asin', 'url', 'store', 'description', 'quantity',
                                                           'quantity_partial', 'stock_type', 'send_date', 'edd_date',
                                                           'best_before', 'condition', 'actual_condition',
                                                           'condition_comments', 'status', 'pick_ticket',
                                                           'collaborator'),
                                          localized_fields=('send_date',), min_num=1, max_num=1)
    TrackingFormSet = inlineformset_factory(Product, Tracking, formset=MyBaseInlineFormSet, fields=('track_number',),
                                            extra=1)
    if pid is None:
        page_type = 1
        page_title = _('Adicionar Produto')
        product_qs = Product.objects.none()
        product_instance = None
    else:
        page_type = 2
        product_filter = Q(pk=pid)
        is_user_perm = has_user_perm(request.user, 'view_users')
        is_collaborator_perm = has_store_perm(request.user, 'collaborator')
        if is_collaborator_perm and request.user.collaborator:
            product_filter &= (Q(user=request.user) | Q(collaborator=request.user.collaborator))
        elif is_user_perm is False:
            product_filter &= Q(user=request.user)
        product_qs = Product.objects.filter(product_filter)
        try:
            product_instance = product_qs[:1].get()
        except Product.DoesNotExist:
            return HttpResponseRedirect(reverse('product_add'))
        page_title = _('Editar Produto')
    kwargs = {'addText': _('Adicionar rastreamento'), 'deleteText': _('Remover rastreamento')}
    if request.method != 'POST':
        product_formset = ProductFormSet(queryset=product_qs)
        tracking_formset = TrackingFormSet(instance=product_instance, prefix='tracking_set', **kwargs)
        context_data = {'title': page_title, 'product_formset': product_formset, 'tracking_formset': tracking_formset,
                        'page_type': page_type}
        if request.GET.get('s') == '1':
            if pid is None:
                success_message = _('Produto inserido com sucesso.')
            else:
                success_message = _('Produto atualizado com sucesso.')
            context_data['success'] = True
            context_data['success_message'] = success_message
        return render(request, 'product_add_edit.html', context_data)
    else:
        product_formset = ProductFormSet(request.POST, queryset=product_qs)
        if product_formset.is_valid():
            with transaction.atomic():
                if pid is None:
                    for product_form in product_formset:
                        product = product_form.save(commit=False)
                        product.status = 1
                        product.user = request.user
                        if product.quantity_partial is None:
                            product.quantity_original = product.quantity_partial = product.quantity
                        elif product.quantity_partial <= 0:
                            product.quantity = product.quantity_partial = 0
                        elif product.quantity_partial > product.quantity:
                            product.quantity = product.quantity_partial
                        product.save()
                        tracking_formset = TrackingFormSet(request.POST, instance=product,
                                                           prefix='tracking_set', **kwargs)
                else:
                    for product_form in product_formset:
                        product = product_form.save(commit=False)
                        product.status = product_instance.status
                        if has_product_perm(request.user, 'change_product_status') is False:
                            product.quantity = product_instance.quantity
                        if product.quantity_partial is None:
                            product.quantity_original = product.quantity_partial = product.quantity
                        elif product.quantity_partial <= 0:
                            product.quantity = product.quantity_partial = 0
                        elif product.quantity_partial > product.quantity:
                            product.quantity = product.quantity_partial
                        product.save()
                    tracking_formset = TrackingFormSet(request.POST, instance=product_instance, prefix='tracking_set',
                                                       **kwargs)
                tracking_formset.save()
            if pid is None:
                return HttpResponseRedirect('%s?s=1' % reverse('product_add'))
            else:
                return HttpResponseRedirect('%s?s=1' % reverse('product_edit', args=[pid]))
        tracking_formset = TrackingFormSet(request.POST, instance=product_instance, prefix='tracking_set', **kwargs)
        return render(request, 'product_add_edit.html', {'title': page_title, 'success': False,
                                                         'product_formset': product_formset,
                                                         'tracking_formset': tracking_formset,
                                                         'page_type': page_type})


@login_required
@require_http_methods(["PUT"])
def product_edit_status(request, pid=None, output=None):
    if has_product_perm(request.user, 'change_product_status') is False:
        if output and output == 'json':
            return HttpResponse(json.dumps({'success': False}),
                                content_type='application/json', status=403)
        else:
            return HttpResponseForbidden()
    request.PUT = QueryDict(request.body)
    try:
        product_filter = Q(pk=pid)
        if has_store_perm(request.user, 'collaborator'):
            if request.user.collaborator:
                product_filter &= Q(collaborator=request.user.collaborator)
            elif request.user.first_name != 'Administrador':
                raise Product.DoesNotExist('Inconsistent collaborator.')
        product = Product.objects.select_related('user').get(product_filter)
        fields_to_update = []
        error_msg = []
        product_quantity_partial = request.PUT.get('product_quantity_partial')
        if product_quantity_partial:
            try:
                product_quantity_partial = int(product_quantity_partial)
                if product.quantity_partial < 0:
                    int('err')
            except ValueError:
                error_msg.append(_('Quantidade deve ser maior ou igual a zero.') % {'qty': product.quantity})
            if product_quantity_partial != product.quantity_partial:
                product.quantity_partial = product_quantity_partial
                fields_to_update.append('quantity_partial')
                if product.quantity_partial == 0 or product.quantity_partial > product.quantity:
                    product.quantity = product.quantity_partial
                    fields_to_update.append('quantity')
        product_best_before = request.PUT.get('product_best_before')
        if product_best_before:
            try:
                product_best_before = datetime.datetime.strptime(product_best_before, str(_('%d/%m/%Y')))
                if product.best_before is None or product.best_before.date() != product_best_before.date():
                    product.best_before = product_best_before
                    fields_to_update.append('best_before')
            except ValueError:
                error_msg.append(_('Data de Vencimento inválida.'))
        elif product.best_before:
            product.best_before = None
            fields_to_update.append('best_before')
        if error_msg:
            return HttpResponse(json.dumps({'success': False, 'error': (_(' ; ').join(error_msg))}),
                                content_type='application/json', status=400)
        if product.quantity == product.quantity_partial and product.quantity == 0 and \
                ShipmentProduct.objects.filter(Q(product__id=product.id) &
                                               ~Q(shipment__status=5) &
                                               Q(shipment__is_archived=False) &
                                               Q(shipment__is_canceled=False)).exists() is False:
            product_status = '99'  # Archived
        else:
            product_status = request.PUT.get('product_status')
        if str(product.status) != product_status:
            fields_to_update.append('status')
            if product_status == '2':
                product.receive_date = datetime.datetime.now()
                fields_to_update.append('receive_date')
        product_status_display = None
        for choice in Product.STATUS_CHOICES:
            if str(choice[0]) == product_status:
                product_status_display = str(choice[1])
                break
        if product_status_display is not None:
            product.status = product_status
        else:
            for choice in Product.STATUS_CHOICES:
                if str(choice[0]) == str(product.status):
                    product_status_display = str(choice[1])
                    break
        product_actual_condition = request.PUT.get('product_actual_condition')
        if str(product.actual_condition) != product_actual_condition:
            fields_to_update.append('actual_condition')
        product_actual_condition_display = None
        for choice in Product.CONDITION_CHOICES:
            if str(choice[0]) == product_actual_condition:
                product_actual_condition_display = str(choice[1])
                break
        if product_actual_condition_display is None:
            product.actual_condition = None
            product_actual_condition_display = ''
        else:
            product.actual_condition = product_actual_condition
        product_condition_comments = request.PUT.get('product_condition_comments')
        if product.condition_comments != product_condition_comments:
            product.condition_comments = product_condition_comments
            fields_to_update.append('condition_comments')
        pick_ticket = False
        product_pick_ticket = request.PUT.get('product_pick_ticket')
        if product.pick_ticket != product_pick_ticket:
            product.pick_ticket = product_pick_ticket.strip()
            pick_ticket = True
        if len(fields_to_update) == 0 and pick_ticket is False:
            raise Product.DoesNotExist
        elif len(fields_to_update) == 0 and pick_ticket:
            product.save(update_fields=['pick_ticket'])
        else:
            fields_to_update.append('pick_ticket')
            with transaction.atomic():
                product.save(update_fields=fields_to_update)
                shipment_products = product.product_set.all()
                for shipment_product in shipment_products:
                    shipment_product.receive_date = product.receive_date
                    shipment_product.save(update_fields=['receive_date'])
            send_email_product_info(request, product, product_status_display, product_actual_condition_display)
        if output and output == 'json':
            product_json = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'quantity': product.quantity,
                'quantity_partial': product.quantity_partial,
                'send_date': formats.date_format(product.send_date, "DATE_FORMAT"),
                'best_before': '' if product.best_before is None else formats.date_format(product.best_before,
                                                                                          "SHORT_DATE_FORMAT"),
                'actual_condition': '' if product.actual_condition is None else product.actual_condition,
                'condition_comments': '' if product.condition_comments is None else product.condition_comments,
                'pick_ticket': '' if product.pick_ticket is None else product.pick_ticket,
                'status': product.status,
                'status_display': product_status_display,
                'show_check': product.user == request.user,
            }
            return HttpResponse(json.dumps({'success': True, 'product': product_json}),
                                content_type='application/json')
        else:
            pass  # TODO retorno de sucesso da edição HTML
    except Product.DoesNotExist:
        if output and output == 'json':
            return HttpResponse(json.dumps({'success': False}),
                                content_type='application/json', status=400)
        else:
            pass  # TODO retorno de erro da edição HTML


@login_required
@require_http_methods(["GET"])
def product_details(request, pid=None):
    if has_product_perm(request.user, 'view_products') is False:
        return HttpResponseForbidden()
    query = Q(pk=pid)
    try:
        is_fetch_user = True
        is_collaborator_perm = has_store_perm(request.user, 'collaborator')
        if is_collaborator_perm and request.user.collaborator:
            query &= (Q(user=request.user) | Q(collaborator=request.user.collaborator))
            is_fetch_user = False
        elif has_user_perm(request.user, 'view_users') is False:
            query &= Q(user=request.user)
            is_fetch_user = False
        if is_fetch_user:
            product = Product.objects.select_related('user').get(query)
        else:
            product = Product.objects.get(query)
        shipment_products = product.product_set.all()
        shipments = ', '.join([str(shipment_product.shipment_id) for shipment_product in shipment_products])
        return render(request, 'product_details.html', {'title': _('Produto'), 'shipments': len(shipment_products),
                                                        'shipments_id': shipments,
                                                        'product': product,
                                                        'product_tracking': product.tracking_set.all()})
    except Product.DoesNotExist:
        pass
    return render(request, 'product_details.html', {'title': _('Produto'), 'shipments': 0})


@login_required
@require_http_methods(["POST"])
def product_delete(request):
    if has_product_perm(request.user, 'delete_product') is False:
        return HttpResponseForbidden()
    request.DELETE = QueryDict(request.body)
    query = Q(pk=request.DELETE.get('pid'))
    is_collaborator_perm = has_store_perm(request.user, 'collaborator')
    if is_collaborator_perm and request.user.collaborator:
        query &= (Q(user=request.user) | Q(collaborator=request.user.collaborator))
    elif has_user_perm(request.user, 'view_users') is False:
        query &= Q(user=request.user)
    try:
        product = Product.objects.get(query)
        shipment_products = product.product_set.all()
        if len(shipment_products) > 0:
            shipments = ', '.join([str(shipment_product.shipment_id) for shipment_product in shipment_products])
            return render(request, 'product_details.html', {'title': _('Produto'), 'shipments': len(shipment_products),
                                                            'shipments_id': shipments, 'show_error': True,
                                                            'product': product,
                                                            'product_tracking': product.tracking_set.all()})
        product.delete()
    except Product.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('product_stock'))


@login_required
@require_http_methods(["GET"])
def product_autocomplete(request):
    if has_product_perm(request.user, 'view_products') is False:
        return HttpResponse(json.dumps([]),
                            content_type='application/json', status=403)
    products_autocomplete = []
    term = request.GET.get('term')
    if term is not None and len(term) >= 3:
        products = Product.objects.filter(name__icontains=term, status=2, user=request.user,
                                          quantity_partial__gt=0, stock_type=1).order_by('id')
        for product in products:
            products_autocomplete.append({'value': product.id, 'label': product.name,
                                          'desc': product.description, 'qty': product.quantity_partial,
                                          'bb': formats.date_format(product.best_before, "SHORT_DATE_FORMAT")
                                          if product.best_before else '',
                                          'lot': False if product.lot_product is None else True,
                                          'asin': product.asin if product.asin else ''})
    return HttpResponse(json.dumps(products_autocomplete),
                        content_type='application/json')


@login_required
@require_http_methods(["GET"])
def product_autocomplete_fbm(request):
    if has_product_perm(request.user, 'view_products') is False:
        return HttpResponse(json.dumps([]),
                            content_type='application/json', status=403)
    products_autocomplete = []
    term = request.GET.get('term')
    if term is not None and len(term) >= 3:
        products = Product.objects.filter(name__icontains=term, status=2, user=request.user,
                                          quantity_partial__gt=0, stock_type=2).order_by('id')
        for product in products:
            products_autocomplete.append({'value': product.id, 'label': product.name,
                                          'desc': product.description, 'qty': product.quantity_partial,
                                          'bb': formats.date_format(product.best_before, "SHORT_DATE_FORMAT")
                                          if product.best_before else '',
                                          'lot': False if product.lot_product is None else True,
                                          'asin': product.asin if product.asin else ''})
    return HttpResponse(json.dumps(products_autocomplete),
                        content_type='application/json')


def send_email_product_info(request, product, product_status_display, product_actual_condition_display):
    email_title = _('Mudança nos dados sobre o seu produto \'%(product)s\'') % {'product': product.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: {}</p>']
                           if product.status == '2' else ['']) +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: {}</p>'] if product.best_before
                           else ['']) +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: {}</p>']) +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: {}</p>']) +
                          (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] if product.status == '2'
                           else ['']) +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = [mark_safe(_('Status do produto: <strong>%(status)s</strong>')
                       % {'status': product_status_display})]
    if product.status == '2':
        texts += [_('Quantidade em estoque na VOI'), product.quantity_partial]
    if product.best_before:
        texts += [_('Data de validade'), formats.date_format(product.best_before, "DATE_FORMAT")]
    texts += [_('Condição do produto no recebimento'), product_actual_condition_display]
    texts += [_('Comentários sobre a condição'), product.condition_comments if product.condition_comments is not None
              else '']
    if product.status == '2':
        texts += [_('Crie seu envio agora mesmo!')]
    texts += [''.join(['https://', request.CURRENT_DOMAIN, reverse('product_stock')]), _('Clique aqui'),
              _('para acessar sua lista de produtos.')]
    email_body = format_html(html_format, *tuple(texts))
    send_email_basic_template_bcc_admins(request, product.user.first_name, [product.user.email], email_title,
                                         email_body, async=True)
