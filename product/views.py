from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db import transaction
from product.models import Product, Tracking
from django.contrib.sites.models import Site
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden
from django.utils import formats, timezone
from django.forms import modelformset_factory, inlineformset_factory
from django.urls import reverse
from utils.helper import MyBaseInlineFormSet, ObjectView, send_email_basic_template_bcc_admins
from product.templatetags.products import has_product_perm
from myauth.templatetags.users import has_user_perm
from django.utils.html import format_html, mark_safe
from django.conf import settings
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
        queries = []
        logger.debug('@@@@@@@@@@@@ PRODUCT STOCK FILTERS @@@@@@@@@@@@@@')
        logger.debug(settings.DEBUG)
        logger.debug(settings.PAYPAL_TEST)
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_name = request.GET.get('name')
        logger.debug(str(filter_name))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_tracking = request.GET.get('tracking')
        logger.debug(str(filter_tracking))
        filter_archived = request.GET.get('archived')
        logger.debug(str(filter_archived))
        filter_values = {
            'status': '',
        }
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if filter_name:
            queries.append(Q(name__icontains=filter_name))
            filter_values['name'] = filter_name
        if is_user_perm and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user) |
                           Q(user__email__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        if filter_tracking:
            queries.append(Q(tracking__track_number=filter_tracking))
            filter_values['tracking'] = filter_tracking
        if filter_archived and filter_archived == 'on':
            filter_values['archived'] = 'checked=checked'
        else:
            queries.append(~Q(status=99))
        logger.debug('@@@@@@@@@@@@ QUERIES @@@@@@@@@@@@@@')
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
    return render(request, 'product_stock.html', {'title': _('Estoque'), 'products': products,
                                                  'filter_values': ObjectView(filter_values)})


@login_required
@require_http_methods(["GET", "POST"])
def product_add_edit(request, pid=None):
    if pid is None and has_product_perm(request.user, 'add_product') is False:
        return HttpResponseForbidden()
    elif pid is not None and has_product_perm(request.user, 'change_product') is False:
        return HttpResponseForbidden()
    ProductFormSet = modelformset_factory(Product, fields=('name', 'description', 'quantity', 'quantity_partial',
                                                           'send_date', 'best_before', 'condition', 'actual_condition',
                                                           'condition_comments'),
                                          localized_fields=('send_date',), min_num=1, max_num=1)
    TrackingFormSet = inlineformset_factory(Product, Tracking, formset=MyBaseInlineFormSet, fields=('track_number',),
                                            extra=1)
    if pid is None:
        page_title = _('Adicionar Produto')
        product_qs = Product.objects.none()
        product_instance = None
    else:
        product_qs = Product.objects.filter(pk=pid)
        try:
            product_instance = product_qs[:1].get()
        except Product.DoesNotExist:
            return HttpResponseRedirect(reverse('product_add'))
        page_title = _('Editar Produto')
    kwargs = {'addText': _('Adicionar rastreamento'), 'deleteText': _('Remover rastreamento')}
    if request.method != 'POST':
        product_formset = ProductFormSet(queryset=product_qs)
        tracking_formset = TrackingFormSet(instance=product_instance, prefix='tracking_set', **kwargs)
        context_data = {'title': page_title, 'product_formset': product_formset, 'tracking_formset': tracking_formset}
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
                            product.quantity_partial = product.quantity
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
                        if product.quantity_partial is None:
                            product.quantity_partial = product.quantity
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
                                                         'tracking_formset': tracking_formset})


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
        product = Product.objects.select_related('user').get(pk=pid)
        if product.user == request.user or has_user_perm(request.user, 'view_users'):
            fields_to_update = []
            error_msg = []
            product_quantity_partial = request.PUT.get('product_quantity_partial')
            if product_quantity_partial:
                try:
                    product.quantity_partial = int(product_quantity_partial)
                    if product.quantity_partial < 0:
                        int('err')
                except ValueError:
                    error_msg.append(_('Quantidade deve ser maior ou igual a zero.') % {'qty': product.quantity})
                fields_to_update.append('quantity_partial')
                if product.quantity_partial == 0 or product.quantity_partial > product.quantity:
                    product.quantity = product.quantity_partial
                    fields_to_update.append('quantity')
            product_best_before = request.PUT.get('product_best_before')
            if product_best_before:
                try:
                    product_best_before = datetime.datetime.strptime(product_best_before, '%d/%m/%Y')
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
            if product.quantity_partial == 0:
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
            if len(fields_to_update) == 0:
                raise Product.DoesNotExist
            product.save(update_fields=fields_to_update)
            send_email_product_info(product, product_status_display, product_actual_condition_display)
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
        if has_user_perm(request.user, 'view_users') is False:
            query &= Q(user=request.user)
            product = Product.objects.get(query)
        else:
            product = Product.objects.select_related('user').get(query)
        product_tracking = Tracking.objects.filter(product=product)
        return render(request, 'product_details.html', {'title': _('Produto'), 'product': product,
                                                        'product_tracking': product_tracking})
    except Product.DoesNotExist:
        pass
    return render(request, 'product_details.html', {'title': _('Produto')})


@login_required
@require_http_methods(["POST"])
def product_delete(request):
    if has_product_perm(request.user, 'delete_product') is False:
        return HttpResponseForbidden()
    request.DELETE = QueryDict(request.body)
    query = Q(pk=request.DELETE.get('pid'))
    if has_user_perm(request.user, 'view_users') is False:
        query &= Q(user=request.user)
    Product.objects.filter(query).delete()
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
                                          quantity_partial__gt=0).order_by('id')
        for product in products:
            products_autocomplete.append({'value': product.id, 'label': product.name,
                                          'desc': product.description, 'qty': product.quantity_partial,
                                          'bb': formats.date_format(product.best_before, "SHORT_DATE_FORMAT")
                                          if product.best_before else ''})
    return HttpResponse(json.dumps(products_autocomplete),
                        content_type='application/json')


def send_email_product_info(product, product_status_display, product_actual_condition_display):
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
    texts += [''.join(['https://', Site.objects.get_current().domain, reverse('product_stock')]), _('Clique aqui'),
              _('para acessar sua lista de produtos.')]
    email_body = format_html(html_format, *tuple(texts))
    send_email_basic_template_bcc_admins(product.user.first_name, [product.user.email], email_title, email_body)
