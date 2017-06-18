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
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from payment.forms import MyPayPalSharedSecretEncryptedPaymentsForm
from django.urls import reverse
from django.contrib.sites.models import Site
from myauth.templatetags.users import has_user_perm
import datetime
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
def store_list(request):
    queries = []
    logger.debug('@@@@@@@@@@@@ STORE FILTERS @@@@@@@@@@@@@@')
    filter_name = request.GET.get('name')
    logger.debug(str(filter_name))
    filter_values = {
        'name': '',
    }
    if filter_name:
        queries.append(Q(name__icontains=filter_name))
        filter_values['name'] = filter_name
    queries.append(Q(status=1))
    logger.debug(str(queries))
    logger.debug(str(len(queries)))
    _lot_list = Lot.objects.extra(where=['EXISTS (SELECT 1 FROM store_lot_groups WHERE store_lot.id = store_lot_groups.'
                                         'lot_id AND store_lot_groups.group_id IN (SELECT U0.id FROM auth_group U0 '
                                         'INNER JOIN myauth_myuser_groups U1 ON (U0.id = U1.group_id) WHERE '
                                         'U1.myuser_id = %s)) OR NOT EXISTS (SELECT 1 FROM store_lot_groups WHERE '
                                         'store_lot.id = store_lot_groups.lot_id)'], params=[request.user.id])
    query = queries.pop()
    for item in queries:
        query &= item
    logger.debug(str(query))
    _lot_list = _lot_list.filter(query).order_by('id')
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


@login_required
@require_http_methods(["GET"])
def store_lot_details(request, pid=None):
    try:
        _lot_details = Lot.objects.extra(where=['EXISTS (SELECT 1 FROM store_lot_groups WHERE store_lot.id = store_lot_'
                                                'groups.lot_id AND store_lot_groups.group_id IN (SELECT U0.id FROM '
                                                'auth_group U0 INNER JOIN myauth_myuser_groups U1 ON '
                                                '(U0.id = U1.group_id) WHERE U1.myuser_id = %s)) OR NOT EXISTS ('
                                                'SELECT 1 FROM store_lot_groups WHERE store_lot.id = '
                                                'store_lot_groups.lot_id)'], params=[request.user.id]).\
            prefetch_related('product_set').get(pk=pid)
    except Lot.DoesNotExist:
        return HttpResponseBadRequest()
    is_sandbox = (request.user.email in settings.PAYPAL_SANDBOX_USERS)
    if settings.PAYPAL_TEST or is_sandbox:
        import time
        current_milli_time = lambda: int(round(time.time() * 1000))
        invoice_id = '_'.join(['B', str(request.user.id), str(pid), 'debug', str(current_milli_time())])
        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX
        paypal_cert_id = settings.PAYPAL_CERT_ID_SANDBOX
        paypal_cert = settings.PAYPAL_CERT_SANDBOX
    else:
        invoice_id = '_'.join(['B', str(request.user.id), str(pid)])
        paypal_business = settings.PAYPAL_BUSINESS
        paypal_cert_id = settings.PAYPAL_CERT_ID
        paypal_cert = settings.PAYPAL_CERT
    paypal_dict = {
        'business': paypal_business,
        'amount': _lot_details.lot_cost,
        'item_name': _lot_details.name,
        'invoice': invoice_id,
        'paymentaction': 'authorization',
        'notify_url': 'https://' + Site.objects.get_current().domain + reverse('paypal-ipn'),
        'return_url': 'https://' + Site.objects.get_current().domain +
                      '%s?p=1' % reverse('store_lot_details', args=[pid]),
        'cancel_return': 'https://' + Site.objects.get_current().domain + reverse('store_lot_details',
                                                                                  args=[pid]),
        # 'custom': 'Custom command!',  # Custom command to correlate to some function later (optional)
    }
    paypal_form = MyPayPalSharedSecretEncryptedPaymentsForm(is_sandbox=is_sandbox,
                                                            initial=paypal_dict,
                                                            paypal_cert=paypal_cert,
                                                            cert_id=paypal_cert_id)
    return render(request, 'store_lot_details.html', {'title': _('Loja'), 'lot': _lot_details,
                                                      'paypal_form': paypal_form})


def store_purchase(request):
    pass


def store_paypal_notification(lot_id, ipn_obj):
    try:
        _lot_details = Lot.objects.select_for_update().get(pk=lot_id)
        if _lot_details.user is not None:
            raise helper.VoidPaymentException()
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


def store_paypal_notification_success(_lot_details, user, ipn_obj, paypal_status_message):
    _lot_details.user = user
    _lot_details.status = 2
    _lot_details.sell_date = datetime.date.today()
    products = _lot_details.product_set.all()
    _lot_details.save(update_fields=['user', 'sell_date'])
    for product in products:
        p = Product.objects.create(name=product.name, description=_('Produto comprado pela Plataforma. '
                                                                    '\'%(lot)s\'') % {'lot': _lot_details.name},
                                   quantity=product.quantity, quantity_partial=product.quantity, status=2,
                                   user=user)
        Tracking.objects.create(track_number=product.identifier, product=p)
    email_title = _('Pagamento confirmado pelo PayPal para o %(item)s') % {'item': ipn_obj.item_name}
    email_message = paypal_status_message
    helper.send_email_basic_template_bcc_admins(_lot_details.user.first_name, [_lot_details.user.email],
                                                email_title, email_message)
