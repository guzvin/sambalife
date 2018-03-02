from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from store.models import Lot
from store.templatetags.lots import calculate_countdown
from product.models import Product
from stock.models import Product as StockProduct
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils import helper
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from payment.forms import MyPayPalSharedSecretEncryptedPaymentsForm
from django.forms import DateField
from django.urls import reverse
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_PENDING, ST_PP_VOIDED
from django.utils import translation
from bisect import bisect
import time
import datetime
import pytz
import json
import logging

logger = logging.getLogger('django')


@require_http_methods(["GET"])
def store_list(request):
    queries = []
    logger.debug('@@@@@@@@@@@@ STORE FILTERS @@@@@@@@@@@@@@')
    filter_value = request.GET.getlist('value')
    logger.debug(str(filter_value))
    filter_rank = request.GET.getlist('rank')
    logger.debug(str(filter_rank))
    filter_roi = request.GET.getlist('roi')
    logger.debug(str(filter_roi))
    filter_values = {
        'roi': [],
    }
    if filter_value:
        if len(filter_value) < 3:
            value_filter = filter_resolver(filter_value)
            logger.debug('@@@@@@@@@@@@@ VALUE FILTER @@@@@@@@@@@@@@')
            logger.debug(value_filter)
            logger.debug(filter_value)
            build_query(queries, value_filter, lte='lot_cost__lte', gte='lot_cost__gte')
        filter_values['value'] = filter_value
    if filter_rank:
        if len(filter_rank) < 4:
            rank_filter = filter_resolver(filter_rank)
            logger.debug('@@@@@@@@@@@@@ RANK FILTER @@@@@@@@@@@@@@')
            logger.debug(rank_filter)
            logger.debug(filter_rank)
            build_query(queries, rank_filter, lte='rank__lte', gte='rank__gte')
        filter_values['rank'] = filter_rank
    if filter_roi:
        if len(filter_roi) < 3:
            roi_filter = filter_resolver(filter_roi)
            logger.debug('@@@@@@@@@@@@@ ROI FILTER @@@@@@@@@@@@@@')
            logger.debug(roi_filter)
            logger.debug(filter_roi)
            build_query(queries, roi_filter, lte='average_roi__lte', gte='average_roi__gte')
        filter_values['roi'] = filter_roi
    # queries.append(Q(status=1) & Q(sell_date=None))
    # logger.debug(str(queries))
    # logger.debug(str(len(queries)))
    # _lot_list = Lot.objects.extra(where=['EXISTS (SELECT 1 FROM store_lot_groups WHERE store_lot.id = store_lot_groups.'
    #                                      'lot_id AND store_lot_groups.group_id IN (SELECT U0.id FROM auth_group U0 '
    #                                      'INNER JOIN myauth_myuser_groups U1 ON (U0.id = U1.group_id) WHERE '
    #                                      'U1.myuser_id = %s)) OR NOT EXISTS (SELECT 1 FROM store_lot_groups WHERE '
    #                                      'store_lot.id = store_lot_groups.lot_id)'], params=[request.user.id])
    queries.append(Q(is_archived=False) & Q(schedule_date=None))
    if queries:
        query = queries.pop()
        for item in queries:
            query &= item
        logger.debug(str(query))
        # _lot_list_available = Lot.objects.filter(query & Q(status=1))
        # _lot_list_sold = Lot.objects.filter(query & Q(status=2)).order_by('-sell_date')[:2]
        # _lot_list = _lot_list_available.union(_lot_list_sold, all=True)
        # _lot_list = Lot.objects.filter(query).order_by('status', '-sell_date')
        _lot_list = Lot.objects.filter(query).order_by('status', '-order_weight', '-sell_date', 'name')
    # else:
    #     _lot_list = Lot.objects.all().order_by('status', '-sell_date', '-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(_lot_list, 20)
    try:
        lots = paginator.page(page)
    except PageNotAnInteger:
        lots = paginator.page(1)
    except EmptyPage:
        lots = paginator.page(paginator.num_pages)
    return render(request, 'store_list.html', {'title': _('Loja'), 'lots': lots,
                                               'filter_values': helper.ObjectView(filter_values)})


def build_query(queries, filter_list, **kwargs):
    i = iter(filter_list)
    clauses = []
    for x in i:
        l, r = x, next(i)
        if l == '-':
            clauses.append(Q(**{kwargs['lte']: r}))
        elif r == '-':
            clauses.append(Q(**{kwargs['gte']: l}))
        else:
            clauses.append((Q(**{kwargs['gte']: l}) & Q(**{kwargs['lte']: r})))
    if clauses:
        query_clause = clauses.pop()
        for clause in clauses:
            query_clause |= clause
        queries.append(query_clause)


def filter_resolver(filters):
    resolved_filter = None
    for r in filters:
        filter_range = r.split(';')
        if resolved_filter is None:
            resolved_filter = filter_range
            continue
        if filter_range[0] == '-':
            try:
                i = resolved_filter.index(filter_range[1])
                resolved_filter[i] = filter_range[0]
            except ValueError:
                resolved_filter = filter_range + resolved_filter
        elif filter_range[1] == '-':
            try:
                i = resolved_filter.index(filter_range[0])
                resolved_filter[i] = filter_range[1]
            except ValueError:
                resolved_filter += filter_range
        else:
            try:
                i = resolved_filter.index(filter_range[0])
                resolved_filter[i] = filter_range[1]
            except ValueError:
                try:
                    i = resolved_filter.index(filter_range[1])
                    resolved_filter[i] = filter_range[0]
                except ValueError:
                    i = bisect(resolved_filter, filter_range[0])
                    resolved_filter = resolved_filter[:i] + filter_range + resolved_filter[i:]
    return resolved_filter


@require_http_methods(["GET"])
def store_lot_details(request, pid=None):
    try:
        _lot_details = Lot.objects.prefetch_related('product_set').get(pk=pid, is_archived=False, schedule_date=None)
    except Lot.DoesNotExist as e:
        logger.error(e)
        return HttpResponseBadRequest()
    has_access = set(request.user.groups.all()) & set(_lot_details.groups.all())
    if not has_access and not (_lot_details.lifecycle_open and request.user.is_authenticated):
        return HttpResponseBadRequest()
    context_data = {'title': _('Loja'), 'lot': _lot_details}
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(_lot_details.user)
    context_data['paypal_form'] = MyPayPalSharedSecretEncryptedPaymentsForm(is_sandbox=is_sandbox,
                                                                            is_render_button=True,
                                                                            origin='store')
    return render(request, 'store_lot_details.html', context_data)


def current_milli_time(): return int(round(time.time() * 1000))


@require_http_methods(["GET"])
def store_pay_form(request, pid=None):
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({'redirect': reverse('user_registration')}), content_type='application/json')
    try:
        # _lot_details = Lot.objects.extra(where=['EXISTS (SELECT 1 FROM store_lot_groups '
        #                                         'WHERE store_lot.id = store_lot_'
        #                                         'groups.lot_id AND store_lot_groups.group_id IN (SELECT U0.id FROM '
        #                                         'auth_group U0 INNER JOIN myauth_myuser_groups U1 ON '
        #                                         '(U0.id = U1.group_id) WHERE U1.myuser_id = %s)) OR NOT EXISTS ('
        #                                         'SELECT 1 FROM store_lot_groups WHERE store_lot.id = '
        #                                         'store_lot_groups.lot_id)'], params=[request.user.id])\
        #     .get(pk=pid, payment_complete=False)
        _lot_details = Lot.objects.get(pk=pid, payment_complete=False, is_archived=False)
    except Lot.DoesNotExist as e:
        logger.error(e)
        return HttpResponseBadRequest()
    has_access = set(request.user.groups.all()) & set(_lot_details.groups.all())
    if not has_access and not (_lot_details.lifecycle_open  and request.user.is_authenticated):
        return HttpResponse(json.dumps({'modal': 'subscribe'}), content_type='application/json')
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(request.user)
    if is_sandbox:
        invoice_id = '_'.join(['B', str(request.user.id), str(pid), 'debug', str(current_milli_time())])
        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX
        paypal_cert_id = settings.PAYPAL_CERT_ID_SANDBOX
        paypal_cert = settings.PAYPAL_CERT_SANDBOX
        paypal_private_cert = settings.PAYPAL_PRIVATE_CERT_SANDBOX
        paypal_public_cert = settings.PAYPAL_PUBLIC_CERT_SANDBOX
        is_sandbox = settings.PAYPAL_SANDBOX_ENDPOINT_LIVE is False
    else:
        invoice_id = '_'.join(['B', str(request.user.id), str(pid)])
        paypal_business = settings.PAYPAL_BUSINESS
        paypal_cert_id = settings.PAYPAL_CERT_ID
        paypal_cert = settings.PAYPAL_CERT
        paypal_private_cert = settings.PAYPAL_PRIVATE_CERT
        paypal_public_cert = settings.PAYPAL_PUBLIC_CERT
    paypal_dict = {
        'business': paypal_business,
        'amount': _lot_details.lot_cost,
        'item_name': _lot_details.name,
        'invoice': invoice_id,
        'paymentaction': 'authorization',
        'notify_url': 'https://' + request.CURRENT_DOMAIN + reverse('paypal-ipn'),
        'return_url': 'https://' + request.CURRENT_DOMAIN +
                      '%s?p=1' % reverse('store_lot_details', args=[pid]),
        'cancel_return': 'https://' + request.CURRENT_DOMAIN + reverse('store_lot_details', args=[pid]),
        # 'custom': 'Custom command!',  # Custom command to correlate to some function later (optional)
    }
    paypal_form = MyPayPalSharedSecretEncryptedPaymentsForm(is_sandbox=is_sandbox,
                                                            initial=paypal_dict,
                                                            paypal_cert=paypal_cert,
                                                            cert_id=paypal_cert_id,
                                                            private_cert=paypal_private_cert,
                                                            public_cert=paypal_public_cert)
    rendered_response = paypal_form.render()
    logger.info(paypal_dict)
    logger.info(rendered_response)
    return HttpResponse(rendered_response)


@login_required
@require_http_methods(["GET"])
def store_purchase(request):
    queries = [Q(user=request.user)]
    logger.debug('@@@@@@@@@@@@ STORE PURCHASE FILTERS @@@@@@@@@@@@@@')
    filter_name = request.GET.get('name')
    logger.debug(str(filter_name))
    filter_date = request.GET.get('date')
    logger.debug(str(filter_date))
    filter_values = {
        'name': '',
    }
    if filter_name:
        queries.append(Q(name__icontains=filter_name))
        filter_values['name'] = filter_name
    if filter_date:
        d = DateField().to_python(filter_date)
        queries.append(Q(sell_date__date=d))
        filter_values['date'] = filter_date
    query = queries.pop()
    for item in queries:
        query &= item
    selected_order = request.GET.get('order')
    orders = {
        'name': '+name',
        'qty': '-qty',
        'purchase': '-purchase',
        'roi': '-roi',
        'rank': '-rank'
    }
    if selected_order is None:
        selected_order = '-purchase'
    orientation = selected_order[:1]
    if orientation == '-':
        new_order = '+'
    else:
        new_order = '-'
        orientation = ''
    orders[str(selected_order[1:])] = new_order + selected_order[1:]
    if selected_order[1:] == 'name':
        order_by = orientation + 'name'
    elif selected_order[1:] == 'qty':
        order_by = orientation + 'products_quantity'
    elif selected_order[1:] == 'purchase':
        order_by = orientation + 'sell_date'
    elif selected_order[1:] == 'roi':
        order_by = orientation + 'average_roi'
    elif selected_order[1:] == 'rank':
        order_by = orientation + 'average_rank'
    else:
        selected_order = '-purchase'
        order_by = '-sell_date'
        orders['purchase'] = '+purchase'
    lots = Lot.objects.filter(query).order_by(order_by)
    page = request.GET.get('page', 1)
    paginator = Paginator(lots, 20)
    try:
        lots = paginator.page(page)
    except PageNotAnInteger:
        lots = paginator.page(1)
    except EmptyPage:
        lots = paginator.page(paginator.num_pages)
    return render(request, 'store_purchase.html', {'title': _('Loja - Minhas Compras'), 'lots': lots,
                                                   'filter_values': helper.ObjectView(filter_values),
                                                   'order_by': helper.ObjectView(orders),
                                                   'selected_order': selected_order})


def store_paypal_notification(lot_id, ipn_obj):
    try:
        _lot_details = Lot.objects.select_for_update().get(pk=lot_id)
        if str(_lot_details.lot_cost) != str(ipn_obj.mc_gross):
            texts = (_('Valor do pagamento não confere com o valor cobrado.'),
                     _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice},
                     _('Valor pago: %(paid)s') % {'paid': ipn_obj.mc_gross},
                     _('Valor cobrado: %(charged)s') % {'charged': _lot_details.lot_cost})
            return None, texts
    except Lot.DoesNotExist:
        texts = (_('Dados do recibo são inválidos.'), _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice})
        return None, texts
    return _lot_details, None


def store_paypal_notification_success(_lot_details, user_id, ipn_obj):
    if ipn_obj.payment_status == ST_PP_PENDING:
        if _lot_details.user is not None and str(_lot_details.user_id) != str(user_id):
            raise helper.VoidPaymentException()
        _lot_details.user_id = user_id
        _lot_details.status = 2
        _lot_details.sell_date = pytz.utc.localize(datetime.datetime.today())
        _lot_details.save(update_fields=['user', 'status', 'sell_date'])
    elif ipn_obj.payment_status == ST_PP_COMPLETED:
        if _lot_details.user is not None and str(_lot_details.user_id) != str(user_id):
            raise helper.PaymentException(_('Usuário do pagamento (%(pay_user)s) não confere com o usuário da '
                                            'autorização (%(auth_user)s).') % {'pay_user': user_id,
                                                                               'auth_user': _lot_details.user_id},)
        _lot_details.payment_complete = True
        _lot_details.save(update_fields=['payment_complete'])
        products = _lot_details.product_set.all()
        for product in products:
            Product.objects.create(name=product.name, description=_('Produto comprado pela Plataforma. '
                                                                    '\'%(lot)s\'') % {'lot': _lot_details.name},
                                   quantity=product.quantity, quantity_partial=product.quantity, status=2,
                                   user_id=user_id, send_date=pytz.utc.localize(datetime.datetime.today()),
                                   receive_date=pytz.utc.localize(datetime.datetime.today()), store=_('VOI'),
                                   condition=product.condition, actual_condition=product.condition,
                                   lot_product=product, asin=product.identifier, collaborator=_lot_details.collaborator,
                                   url=product.url)
    elif ipn_obj.payment_status == ST_PP_VOIDED and str(_lot_details.user_id) == str(user_id):
        _lot_details.user = None
        _lot_details.status = 1
        _lot_details.sell_date = None
        _lot_details.payment_complete = False
        _lot_details.save(update_fields=['user', 'status', 'sell_date', 'payment_complete'])


def store_paypal_notification_post_transaction(request, _lot_details, user, ipn_obj, paypal_status_message):
    if ipn_obj.payment_status == ST_PP_PENDING:
        ipn_obj.complete_authorization()
        email_title = _('Pagamento PENDENTE pelo PayPal para o item \'%(item)s\'') % {'item': ipn_obj.item_name}
        texts = (_('Foi enviada solicitação para o PayPal completar este pagamento, caso um e-mail de confirmação não'
                   ' chegue nos próximos minutos verifique se ocorreu algo de errado.'),)
        email_message = _(helper._html_format(*texts)) + paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, _('Administrador'), None, email_title, email_message,
                                                    async=True)
    elif ipn_obj.payment_status == ST_PP_COMPLETED:
        collaborator_instructions, lang = False, translation.get_language()
        email_title = _('Pagamento CONFIRMADO pelo PayPal para o item \'%(item)s\'') % {'item': ipn_obj.item_name}
        texts = (_('Seu pagamento foi confirmado, obrigado! Os itens já se encontram em seu estoque.'),
                 _('O endereço a ser inserido no FROM dos labels das caixas de seus produtos é:'),
                 _('920 Lafayette Rd') if _lot_details.collaborator is None else _lot_details.collaborator.address_1,
                 _('Seabrook, NH 03874') if _lot_details.collaborator is None else _lot_details.collaborator.address_2,)
        if _lot_details.collaborator and \
                (lang == 'pt' and _lot_details.collaborator.instructions) or \
                (lang != 'pt' and _lot_details.collaborator.instructions_en):
            collaborator_instructions = True
            texts += (_('Seguem algumas instruções do colaborador:'),)
            if lang == 'pt':
                texts += (_lot_details.collaborator.instructions,)
            else:
                texts += (_lot_details.collaborator.instructions_en,)
        texts += (_('Todo o procedimento desde a compra até o redirecionamento de seus produtos você encontra aqui:'),
                  ''.join(['https://', request.CURRENT_DOMAIN,
                           _('/pt/ajuda/voi-services-da-compra-ao-envio-para-amazon.pdf')]),
                  _('Tutorial Plataforma'),
                  _('GARANTA A GRATUIDADE NO ENVIO DE SEUS PRODUTOS'),
                  _('Para o usuário usufruir do redirecionamento grátis, todos os produtos do lote adquirido, deverão '
                    'ser enviados para a amazon, em um prazo de até 3 dias úteis. Caso o tempo de envio supere a '
                    'gratuidade, serão aplicadas as seguintes regras de cobrança para a realização do envio:'),
                  _('- Produto no estoque VOI S a partir do quarto dia até 10 dias: USD 1,29 por unidade do produto;'),
                  _('- Produto no estoque VOI S de 11 até 20 dias: USD 1,49 por unidade do produto;'),
                  _('- Produto no estoque VOI S de 21 até 30 dias: USD 1,99 por unidade do produto; e'),
                  _('- Após 30 dias entrar em contato com o nosso suporte.'),)
        html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                              ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}<br>{}<br>{}</p>'] +
                              (['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}<br>{}</p>']
                              if collaborator_instructions else []) +
                              ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'
                               '<br>'
                               '<a href="{}">{}</a></p>'] +
                              ['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'
                               '<br>'
                               '<br>'
                               '{}<br>{}<br>{}<br>{}<br>{}</p>'])
        email_message = _(helper._html_format(*texts, custom_html_format=html_format)) + paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, user.first_name, [user.email], email_title, email_message,
                                                    async=True)
    elif ipn_obj.payment_status == ST_PP_VOIDED:
        email_title = _('CANCELAMENTO do pagamento confirmado pelo PayPal para o item '
                        '\'%(item)s\'') % {'item': ipn_obj.item_name}
        email_message = paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, user.first_name, [user.email], email_title, email_message,
                                                    async=True)


@login_required
@require_http_methods(["GET"])
def product_name_autocomplete(request):
    term = request.GET.get('term')
    return _product_autocomplete(StockProduct.objects.filter(name__icontains=term).order_by('name'))


@login_required
@require_http_methods(["GET"])
def product_asin_autocomplete(request):
    term = request.GET.get('term')
    return _product_autocomplete(StockProduct.objects.filter(identifier__icontains=term).order_by('name'))


def _product_autocomplete(qs):
    products_autocomplete = []
    for product in qs:
        products_autocomplete.append({'label': ' - '.join([str(product.id), product.identifier, product.name]),
                                      'id': str(product.id),
                                      'name': product.name, 'identifier': product.identifier, 'url': product.url,
                                      'buy_price': str(product.buy_price), 'sell_price': str(product.sell_price),
                                      'quantity': product.quantity, 'fba_fee': str(product.fba_fee),
                                      'amazon_fee': str(product.amazon_fee),
                                      'shipping_cost': str(product.shipping_cost),
                                      'product_cost': str(product.product_cost),
                                      'profit_per_unit': str(product.profit_per_unit),
                                      'total_profit': str(product.total_profit),
                                      'roi': str(product.roi), 'rank': product.rank,
                                      'voi_value': str(product.voi_value), 'condition': product.condition,
                                      'redirect_services': [redirect_service.id for redirect_service in
                                                            product.redirect_services.all()],
                                      'notes': product.notes})
    return HttpResponse(json.dumps(products_autocomplete),
                        content_type='application/json')


@require_http_methods(["GET"])
def public_countdown(request, pid=None):
    c = calculate_countdown(request.user, Lot.objects.get(pk=pid), force_is_open=True)
    return HttpResponse(json.dumps({} if c is None else {'public_countdown': c}),
                        content_type='application/json')
