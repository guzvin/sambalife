from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseForbidden
from shipment.views import calculate_shipment
from shipment.models import Shipment, Product as ShipmentProduct, ProductService
from service.templatetags.services import has_service_perm
from django.utils import formats
from django.utils.encoding import force_text
import uuid
import json
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET", "POST"])
def service_product(request, pid=None):
    cost = 0
    services_product_json = []
    product_services = 0
    if request.method == 'GET':
        puid = request.GET.get('puid')
        services_product = ProductService.objects.filter(product_id=pid, product__uid=puid).order_by('service__name')
        product_services = len(services_product)
        for _service_product in services_product:
            services_product_json.append({'service_id': _service_product.service_id,
                                          'service_price': str(_service_product.price)})
    elif has_service_perm(request.user, 'add_product') is False:
        return HttpResponseForbidden()
    else:
        selected_services = request.POST.getlist('service')
        product_services = len(selected_services)
        shipment_product_uid = request.POST.get('shipment_product_uid')
        logger.debug(selected_services)
        ShipmentProduct.objects.get(id=pid, uid=uuid.UUID(shipment_product_uid))
        ProductService.objects.filter(product_id=pid).delete()
        for selected_service in selected_services:
            service_price = request.POST.get('price' + selected_service)
            logger.debug(service_price)
            ProductService.objects.bulk_create([
                ProductService(product_id=pid, service_id=selected_service, price=service_price)
            ])
        shipment = Shipment.objects.raw('select shipment_shipment.id as id, shipment_shipment.user_id as user_id '
                                        'from shipment_shipment '
                                        'inner join shipment_product '
                                        'on shipment_shipment.id = shipment_product.shipment_id '
                                        'and shipment_product.id = %s', [pid])[0]
        shipment_products = shipment.product_set.all()
        ignore_http_response, cost = calculate_shipment(shipment_products, shipment.user_id)
        logger.debug(cost)
    return HttpResponse(json.dumps({'new_cost': force_text(formats.number_format(round(cost, 2), use_l10n=True,
                                                                                 decimal_pos=2)),
                                    'new_cost_raw': round(cost, 2),
                                    'products': services_product_json, 'v': product_services}),
                        content_type='application/json')
