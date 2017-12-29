from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from store.models import Lot
from product.models import Product, Tracking
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils import helper
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from payment.forms import MyPayPalSharedSecretEncryptedPaymentsForm
from django.urls import reverse
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_PENDING, ST_PP_VOIDED
from django.db import transaction
from store.models import Config
from bisect import bisect
import time
import datetime
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
    if queries:
        query = queries.pop()
        for item in queries:
            query &= item
        logger.debug(str(query))
        _lot_list = Lot.objects.filter(query).order_by('-id', 'status', '-sell_date')
    else:
        _lot_list = Lot.objects.all().order_by('-id', 'status', '-sell_date')
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
        _lot_details = Lot.objects.prefetch_related('product_set').get(pk=pid)
    except Lot.DoesNotExist as e:
        logger.error(e)
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
    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({'redirect': reverse('user_registration')}), content_type='application/json')
    config = Config.objects.first()
    if config:
        if not request.user.groups.filter(pk=config.default_group.id).exists():
            return HttpResponse(json.dumps({'modal': 'subscribe'}), content_type='application/json')
    try:
        with transaction.atomic():
            _lot_details = Lot.objects.extra(where=['EXISTS (SELECT 1 FROM store_lot_groups '
                                                    'WHERE store_lot.id = store_lot_'
                                                    'groups.lot_id AND store_lot_groups.group_id IN (SELECT U0.id FROM '
                                                    'auth_group U0 INNER JOIN myauth_myuser_groups U1 ON '
                                                    '(U0.id = U1.group_id) WHERE U1.myuser_id = %s)) OR NOT EXISTS ('
                                                    'SELECT 1 FROM store_lot_groups WHERE store_lot.id = '
                                                    'store_lot_groups.lot_id)'], params=[request.user.id]). \
                select_for_update().get(pk=pid, payment_complete=False)
    except Lot.DoesNotExist as e:
        logger.error(e)
        return HttpResponseBadRequest()
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(_lot_details.user)
    if is_sandbox:
        invoice_id = '_'.join(['B', str(request.user.id), str(pid), 'debug', str(current_milli_time())])
        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX
        paypal_cert_id = settings.PAYPAL_CERT_ID_SANDBOX
        paypal_cert = settings.PAYPAL_CERT_SANDBOX
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
    return render(request, 'store_purchase.html', {'title': _('Loja - Minhas Compras')})


def store_paypal_notification(lot_id, ipn_obj):
    try:
        _lot_details = Lot.objects.select_for_update().get(pk=lot_id)
        if str(_lot_details.lot_cost) != str(ipn_obj.payment_gross):
            texts = (_('Valor do pagamento não confere com o valor cobrado.'),
                     _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice},
                     _('Valor pago: %(paid)s') % {'paid': ipn_obj.payment_gross},
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
        _lot_details.sell_date = datetime.date.today()
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
            p = Product.objects.create(name=product.name, description=_('Produto comprado pela Plataforma. '
                                                                        '\'%(lot)s\'') % {'lot': _lot_details.name},
                                       quantity=product.quantity, quantity_partial=product.quantity, status=2,
                                       user_id=user_id)
            Tracking.objects.create(track_number=product.identifier, product=p)
    elif ipn_obj.payment_status == ST_PP_VOIDED and str(_lot_details.user_id) == str(user_id):
        _lot_details.user = None
        _lot_details.status = 1
        _lot_details.sell_date = None
        _lot_details.payment_complete = True
        _lot_details.save(update_fields=['user', 'status', 'sell_date', 'payment_complete'])


def store_paypal_notification_post_transaction(request, _lot_details, ipn_obj, paypal_status_message):
    if ipn_obj.payment_status == ST_PP_PENDING:
        ipn_obj.complete_authorization()
        email_title = _('Pagamento PENDENTE pelo PayPal para o item \'%(item)s\'') % {'item': ipn_obj.item_name}
        texts = (_('Foi enviada solicitação para o PayPal completar este pagamento, caso um e-mail de confirmação não'
                   ' chegue nos próximos minutos verifique se ocorreu algo de errado.'),)
        email_message = _(helper._html_format(*texts)) + paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, _('Administrador'), None, email_title, email_message,
                                                    async=True)
    elif ipn_obj.payment_status == ST_PP_COMPLETED:
        email_title = _('Pagamento CONFIRMADO pelo PayPal para o item \'%(item)s\'') % {'item': ipn_obj.item_name}
        texts = (_('Seu pagamento foi confirmado, obrigado! Os itens já se encontram em seu estoque.'),)
        email_message = _(helper._html_format(*texts)) + paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, _lot_details.user.first_name, [_lot_details.user.email],
                                                    email_title, email_message, async=True)
    elif ipn_obj.payment_status == ST_PP_VOIDED:
        email_title = _('CANCELAMENTO do pagamento confirmado pelo PayPal para o item '
                        '\'%(item)s\'') % {'item': ipn_obj.item_name}
        email_message = paypal_status_message
        helper.send_email_basic_template_bcc_admins(request, _lot_details.user.first_name, [_lot_details.user.email],
                                                    email_title, email_message, async=True)
