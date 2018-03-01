from django.db import transaction, models
from django.urls import reverse
from django.utils.html import format_html
from django.utils import translation
from django.utils.translation import ugettext as _
from django.http import HttpRequest
from shipment.models import Shipment
from shipment.views import cancel_shipment
from product.models import Product
from utils.models import Params
from store.models import Lot
from store.admin import LotAdmin
from stock.models import Product as ProductStock
from utils import helper
import datetime
import logging

logger = logging.getLogger('django')


def archive_shipped_shipments():
    Shipment.objects.filter(is_archived=False, status=5).update(is_archived=True)


def price_warning():
    params = Params.objects.first()
    if params is None:
        return
    all_products = Product.objects.extra(where=['EXISTS (SELECT 1 FROM shipment_product INNER JOIN shipment_shipment '
                                                'ON shipment_product.shipment_id = shipment_shipment.id '
                                                'WHERE product_product.id = shipment_product.product_id '
                                                'AND shipment_shipment.status < 4 '
                                                'AND shipment_shipment.is_archived = false '
                                                'AND shipment_shipment.is_canceled = false) '
                                                'OR (NOT EXISTS (SELECT 1 FROM shipment_product '
                                                'WHERE product_product.id = shipment_product.product_id) '
                                                'AND product_product.status=2)'])\
        .select_related('user').order_by('user')
    time_period_one = params.time_period_one
    time_period_two = params.time_period_two
    time_period_three = params.time_period_three
    current_user = None
    products_tier_one_warning = None
    products_tier_two_warning = None
    products_tier_two = None
    products_tier_three_warning = None
    products_tier_three = None
    products_tier_abandoned = None
    emails = ()
    for product in all_products:
        if product.user != current_user:
            if current_user is not None:
                translation.activate(current_user.language_code)
                request = HttpRequest()
                request.LANGUAGE_CODE = translation.get_language()
                request.CURRENT_DOMAIN = _('vendedorinternacional.net')
                tier_two_price = params.redirect_factor_two
                tier_three_price = params.redirect_factor_three
                if current_user.partner:
                    tier_two_price += params.partner_cost
                    tier_three_price += params.partner_cost
                for tier_product in products_tier_one_warning:
                    texts = (_warning_message(tier_product[1], time_period_one, tier_two_price),)
                    emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
                for tier_product in products_tier_two_warning:
                    texts = (_warning_message(tier_product[1], (time_period_one + time_period_two), tier_three_price),)
                    emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
                for tier_product in products_tier_two:
                    texts = (_price_change_message(tier_two_price, tier_product[1], time_period_two),)
                    emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
                for tier_product in products_tier_three_warning:
                    texts = (_('Seu produto encontra-se há %(days)s dias no estoque VOI. Fique atento, pois se passar '
                               'do período de %(period)s dias ele será considerado abandonado.')
                             % {'days': tier_product[1],
                                'period': (time_period_one + time_period_two + time_period_three)},)
                    emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
                for tier_product in products_tier_three:
                    texts = (_price_change_message(tier_three_price, tier_product[1], time_period_three),)
                    emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
                for tier_product in products_tier_abandoned:
                    emails += (_send_email_abandoned(request, tier_product[0], tier_product[1], current_user),)
            current_user = product.user
            products_tier_one_warning = []
            products_tier_two_warning = []
            products_tier_two = []
            products_tier_three_warning = []
            products_tier_three = []
            products_tier_abandoned = []
        logger.debug('===== product =====')
        logger.debug(product.name)
        logger.debug(product.receive_date)
        elapsed = datetime.datetime.now(datetime.timezone.utc) - product.receive_date
        elapsed = elapsed.days
        logger.debug(elapsed)
        if elapsed > 29 and time_period_one:
            if elapsed <= time_period_one:
                if elapsed % 10 == 0 or elapsed == time_period_one:
                    products_tier_one_warning.append([product, elapsed])
            elif time_period_two:
                if elapsed <= time_period_one + time_period_two:
                    if elapsed == time_period_one + 1:
                        products_tier_two.append([product, elapsed])
                    elif elapsed % 10 == 0 or elapsed == time_period_one + time_period_two:
                        products_tier_two_warning.append([product, elapsed])
                elif time_period_three:
                    if elapsed <= time_period_one + time_period_two + time_period_three:
                        if elapsed == time_period_one + time_period_two + 1:
                            products_tier_three.append([product, elapsed])
                        elif elapsed % 10 == 0 or elapsed == time_period_one + time_period_two + time_period_three:
                            products_tier_three_warning.append([product, elapsed])
                    else:
                        products_tier_abandoned.append([product, elapsed])
                        update_fields = ['status', 'user']
                        shipment_products = product.product_set.filter(shipment__status__lt=4,
                                                                       shipment__is_archived=False,
                                                                       shipment__is_canceled=False)
                        for shipment_product in shipment_products:
                            with transaction.atomic():
                                try:
                                    shipment = Shipment.objects.select_for_update().get(pk=shipment_product.shipment_id,
                                                                                        status__lt=4, is_archived=False,
                                                                                        is_canceled=False)
                                    cancel_shipment(shipment)
                                except Shipment.DoesNotExist:
                                    continue
                            product.status = 100
                            product.user = None
                            product.save(update_fields=update_fields)
        logger.debug('========================')
    if current_user is not None:
        translation.activate(current_user.language_code)
        request = HttpRequest()
        request.LANGUAGE_CODE = translation.get_language()
        request.CURRENT_DOMAIN = _('vendedorinternacional.net')
        tier_two_price = params.redirect_factor_two
        tier_three_price = params.redirect_factor_three
        if current_user.partner:
            tier_two_price += params.partner_cost
            tier_three_price += params.partner_cost
        for tier_product in products_tier_one_warning:
            texts = (_warning_message(tier_product[1], time_period_one, tier_two_price),)
            emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
        for tier_product in products_tier_two_warning:
            texts = (_warning_message(tier_product[1], (time_period_one + time_period_two), tier_three_price),)
            emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
        for tier_product in products_tier_two:
            texts = (_price_change_message(tier_two_price, tier_product[1], time_period_two),)
            emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
        for tier_product in products_tier_three_warning:
            texts = (_('Seu produto encontra-se há %(days)s dias no estoque VOI. Fique atento, pois se passar '
                       'do período de %(period)s dias ele será considerado abandonado.')
                     % {'days': tier_product[1],
                        'period': (time_period_one + time_period_two + time_period_three)},)
            emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
        for tier_product in products_tier_three:
            texts = (_price_change_message(tier_three_price, tier_product[1], time_period_three),)
            emails += (_send_email_warning(request, tier_product[0], current_user, *texts),)
        for tier_product in products_tier_abandoned:
            emails += (_send_email_abandoned(request, tier_product[0], tier_product[1], current_user),)
    if emails:
        helper.send_email(emails, bcc_admins=True, async=True)


def _warning_message(days, period, value):
    return _('Seu produto encontra-se há %(days)s dias no estoque VOI. Fique atento, pois se passar do período de '
             '%(period)s dias o valor por unidade deste produto passará para USD %(value)s.') \
           % {'days': days, 'period': period, 'value': value}


def _price_change_message(value, days, days2):
    return _('O valor unitário deste produto passou para USD %(value)s. Ele encontra-se há %(days)s dias no estoque '
             'VOI. Não perca o próximo prazo que vence em %(days2)s dias.') \
           % {'value': value, 'days': days, 'days2': days2}


def _send_email_warning(request, product, user, *texts):
    email_title = _('Mensagem importante sobre seu produto \'%(product)s\'') % {'product': product.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts += (''.join(['https://', request.CURRENT_DOMAIN, reverse('product_stock')]),
              _('Clique aqui'), _('para acessar sua lista de produtos e criar seus envios agora mesmo!'),)
    email_body = format_html(html_format, *texts)
    return helper.build_basic_template_email_tuple(request, user.first_name, [user.email], email_title, email_body)


def _send_email_abandoned(request, product, days, user):
    email_title = _('Mensagem importante sobre o produto \'%(product)s\'') % {'product': product.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Este produto, ID %(id)s, não consta mais em sua lista, ele foi considerado abandonado, pois já '
               'se encontra há %(days)s dias no estoque VOI.') % {'id': product.id, 'days': days},)
    texts += (''.join(['https://', request.CURRENT_DOMAIN, '/', _('termos-e-condicoes-de-uso/')]),
              _('Clique aqui'), _('para acessar nossos termos e condições de uso.'),)
    email_body = format_html(html_format, *texts)
    return helper.build_basic_template_email_tuple(request, user.first_name, [user.email], email_title, email_body)


def check_scheduled_lots():
    lots = Lot.objects.filter(schedule_date__lte=datetime.datetime.now(datetime.timezone.utc), is_fake=False,
                              is_archived=False, status=1, payment_complete=False)
    for lot in lots:
        LotAdmin.email_new_lot(lot)
    if lots:
        lots.update(schedule_date=None)


def check_lifecycle_lots():
    current_date = datetime.datetime.now(datetime.timezone.utc)
    one_day = current_date - datetime.timedelta(days=1)
    three_days = current_date - datetime.timedelta(days=3)
    # one_day = current_date - datetime.timedelta(minutes=2)
    # three_days = current_date - datetime.timedelta(minutes=4)
    lots = Lot.objects.filter(lifecycle_date__lte=three_days, lifecycle=2, lifecycle_open=True, is_fake=False,
                              is_archived=False, status=1, payment_complete=False)
    logger.debug('THREE DAYS!!!!!!!!!!!!!!!!!!!!!!!')
    logger.debug(lots)
    if lots:
        products_list = []
        for lot in lots:
            products_list.append(lot.product_set.all())
        lots.update(lifecycle_date=None, lifecycle=3, lifecycle_open=False, is_archived=True)
        for products in products_list:
            for product in products:
                ProductStock.objects.filter(pk=product.product_stock_id)\
                    .update(quantity=models.F('quantity') + product.quantity)
    lots = Lot.objects.filter(lifecycle_date__lte=one_day, lifecycle=2, lifecycle_open=False, is_fake=False,
                              is_archived=False, status=1, payment_complete=False)
    logger.debug('ONE DAY!!!!!!!!!!!!!!!!!!!!!!!')
    logger.debug(lots)
    for lot in lots:
        LotAdmin.email_lifecycle_lot(lot)
    if lots:
        lots.update(lifecycle_open=True)
