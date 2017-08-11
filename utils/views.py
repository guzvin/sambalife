from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from shipment.models import Shipment
from utils.models import Accounting, AccountingPartner, Params
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from utils.helper import resolve_price_value
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
@transaction.atomic
def close_accounting(request):
    shipments = Shipment.objects.select_related('user').filter(status=5, accounting=None)
    partners = []
    accounting = Accounting()
    accounting.user = request.user
    accounting.ipaddress = request.META.get('REMOTE_ADDR', '')
    accounting.save()
    try:
        params = Params.objects.first()
        fgr_cost = float(params.fgr_cost)
        partner_cost = float(params.partner_cost)
        base_price = float(params.redirect_factor)
    except Params.DoesNotExist:
        fgr_cost = float(settings.DEFAULT_FGR_COST)
        partner_cost = float(settings.DEFAULT_PARTNER_COST)
        base_price = float(settings.DEFAULT_REDIRECT_FACTOR)
    for shipment in shipments:
        shipment.accounting = accounting
        shipment.save()
        accounting_partner = next((p for p in partners if p.partner == 'fgr'), None)
        if accounting_partner:
            accounting_partner.value = round(accounting_partner.value +
                                             _shipment_products_cost(shipment.product_set.all(), base_price, fgr_cost),
                                             2)
            accounting_partner.total_products += shipment.total_products
        else:
            accounting_partner = AccountingPartner()
            accounting_partner.partner = 'fgr'
            accounting_partner.value = round(_shipment_products_cost(shipment.product_set.all(), base_price, fgr_cost),
                                             2)
            accounting_partner.total_products = shipment.total_products
            accounting_partner.accounting = accounting
            partners.append(accounting_partner)
        user_model = get_user_model()
        try:
            shipment_user = user_model.objects.select_related('partner').get(pk=shipment.user.id)
            partner = shipment_user.partner
        except user_model.DoesNotExist:
            partner = None
        if partner:
            accounting_partner = next((p for p in partners if p.partner == partner.identity), None)
            if accounting_partner:
                accounting_partner.value = round(accounting_partner.value + partner_cost * shipment.total_products, 2)
                accounting_partner.total_products += shipment.total_products
            else:
                accounting_partner = AccountingPartner()
                accounting_partner.partner = partner.identity
                accounting_partner.value = round(partner_cost * shipment.total_products, 2)
                accounting_partner.total_products = shipment.total_products
                accounting_partner.accounting = accounting
                partners.append(accounting_partner)
    for accounting_partner in partners:
        accounting_partner.save()
    return HttpResponseRedirect(reverse('admin:utils_accounting_change', args=[accounting.id]))


def _shipment_products_cost(products, base_price, base_cost):
    cost = 0
    for product in products:
        price = resolve_price_value(product.receive_date)
        cost += (base_cost + ((price - base_price) / 2)) * product.quantity
    return cost
