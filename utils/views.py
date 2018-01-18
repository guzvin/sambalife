from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from shipment.models import Shipment
from utils.models import Accounting, AccountingPartner, Params
from django.db import transaction
from django.conf import settings
from django.template.response import TemplateResponse
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
@transaction.atomic
def close_accounting(request, simulate=False, sandbox=False):
    params = Params.objects.first()
    if params:
        fgr_cost = params.fgr_cost
    else:
        fgr_cost = settings.DEFAULT_FGR_COST
    shipments = Shipment.objects.select_related('user', 'user__partner').filter(status=5, is_sandbox=sandbox,
                                                                                accounting=None)
    partners = []
    accounting = Accounting()
    accounting.user = request.user
    accounting.ipaddress = request.META.get('REMOTE_ADDR', '')
    if simulate is False:
        accounting.save()
    for shipment in shipments:
        if simulate is False:
            shipment.accounting = accounting
            shipment.save()
        accounting_partner = next((p for p in partners if p.partner == 'fgr'), None)
        if accounting_partner:
            accounting_partner.value = accounting_partner.value + _shipment_products_cost(shipment.product_set.all(),
                                                                                          fgr_cost)
            accounting_partner.total_products += shipment.total_products
        else:
            accounting_partner = AccountingPartner()
            accounting_partner.partner = 'fgr'
            accounting_partner.value = _shipment_products_cost(shipment.product_set.all(), fgr_cost)
            accounting_partner.total_products = shipment.total_products
            accounting_partner.accounting = accounting
            partners.append(accounting_partner)
        if shipment.user.partner:
            cost = 0
            if shipment.user.partner.cost:
                cost += shipment.user.partner.cost
            accounting_partner = next((p for p in partners if p.partner == shipment.user.partner.identity), None)
            if accounting_partner:
                accounting_partner.value = accounting_partner.value + cost * shipment.total_products
                accounting_partner.total_products += shipment.total_products
            else:
                accounting_partner = AccountingPartner()
                accounting_partner.partner = shipment.user.partner.identity
                accounting_partner.value = cost * shipment.total_products
                accounting_partner.total_products = shipment.total_products
                accounting_partner.accounting = accounting
                partners.append(accounting_partner)
    for accounting_partner in partners:
        accounting_partner.value = round(accounting_partner.value, 2)
        if simulate is False:
            accounting_partner.save()
    if simulate is False:
        return HttpResponseRedirect(reverse('admin:utils_accounting_change', args=[accounting.id]))
    return accounting, partners


def _shipment_products_cost(products, base_cost):
    cost = 0
    for product in products:
        price = product.cost
        logger.debug('@@@@@@@@@@@@@ Product COST Product COST Product COST @@@@@@@@@@@@@@@@')
        logger.debug(price)
        if price:
            cost += (base_cost + (price / 2)) * product.quantity
        else:
            cost += base_cost * product.quantity
    return cost
