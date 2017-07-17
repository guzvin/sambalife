from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from shipment.models import Shipment
from utils.models import Accounting, AccountingPartner, Params
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
@transaction.atomic
def close_accounting(request):
    shipments = Shipment.objects.select_for_update().select_related('user').filter(status=5, accounting=None)
    partners = []
    accounting = Accounting()
    accounting.user = request.user
    accounting.ipaddress = request.META.get('REMOTE_ADDR', '')
    accounting.save()
    try:
        params = Params.objects.first()
        fgr_cost = float(params.fgr_cost)
        partner_cost = float(params.partner_cost)
    except Params.DoesNotExist:
        fgr_cost = float(settings.DEFAULT_FGR_COST)
        partner_cost = float(settings.DEFAULT_PARTNER_COST)
    for shipment in shipments:
        shipment.accounting = accounting
        shipment.save()
        accounting_partner = next((p for p in partners if p.partner == 'fgr'), None)
        if accounting_partner:
            accounting_partner.total_products += shipment.total_products
        else:
            accounting_partner = AccountingPartner()
            accounting_partner.partner = 'fgr'
            accounting_partner.value = fgr_cost
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
                accounting_partner.total_products += shipment.total_products
            else:
                accounting_partner = AccountingPartner()
                accounting_partner.partner = partner.identity
                accounting_partner.value = partner_cost
                accounting_partner.total_products = shipment.total_products
                accounting_partner.accounting = accounting
                partners.append(accounting_partner)
    for accounting_partner in partners:
        accounting_partner.value *= accounting_partner.total_products
        accounting_partner.save()
    return HttpResponseRedirect(reverse('admin:utils_accounting_change', args=[accounting.id]))
