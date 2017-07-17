from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from shipment.models import Shipment
from utils.models import Accounting, AccountingPartner
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
@transaction.atomic
def close_accounting(request):
    shipments = Shipment.objects.select_for_update().select_related('user').filter(status=5, accounting=None, id__lt=146)
    partners = []
    accounting = Accounting()
    accounting.user = request.user
    accounting.ipaddress = request.META.get('REMOTE_ADDR', '')
    accounting.save()
    for shipment in shipments:
        shipment.accounting = accounting
        shipment.save()
        accounting_partner = next((p for p in partners if p.partner == 'fgr'), None)
        if accounting_partner:
            accounting_partner.total_products += shipment.total_products
        else:
            accounting_partner = AccountingPartner()
            accounting_partner.partner = 'fgr'
            accounting_partner.value = 0.29  # TODO deixar parametrizavel
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
                accounting_partner.value = 0.20  # TODO deixar parametrizavel
                accounting_partner.total_products = shipment.total_products
                accounting_partner.accounting = accounting
                partners.append(accounting_partner)
    for accounting_partner in partners:
        accounting_partner.value *= accounting_partner.total_products
        accounting_partner.save()
    return HttpResponseRedirect(reverse('admin:utils_accounting_change', args=[accounting.id]))
