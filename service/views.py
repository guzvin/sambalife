from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseForbidden
from shipment.views import calculate_shipment
from shipment.models import Shipment, Product as ShipmentProduct, ProductService, ShipmentService
from shipment.templatetags.shipments import has_shipment_perm
from service.models import Service
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
    product_services_json = []
    if request.method == 'GET':
        puid = request.GET.get('puid')
        product_services = ProductService.objects.filter(product_id=pid, product__uid=puid).order_by('service__name')
        product_services_size = len(product_services)
        for product_service in product_services:
            product_services_json.append({'service_id': product_service.service_id,
                                          'service_price': str(product_service.price)})
    elif has_shipment_perm(request.user, 'add_productservice') is False:
        return HttpResponseForbidden()
    else:
        selected_services = request.POST.getlist('service')
        product_services_size = len(selected_services)
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
        ignore_http_response, cost = calculate_shipment(shipment, shipment_products, shipment.user_id)
        logger.debug(cost)
    return HttpResponse(json.dumps({'new_cost': force_text(formats.number_format(round(cost, 2), use_l10n=True,
                                                                                 decimal_pos=2)),
                                    'new_cost_raw': round(cost, 2),
                                    'products': product_services_json, 'v': product_services_size}),
                        content_type='application/json')


@login_required
@require_http_methods(["GET", "POST"])
def service_shipment(request, sid=None):
    cost = 0
    shipment_services_json = []
    if request.method == 'GET':
        shipment_services = ShipmentService.objects.filter(shipment_id=sid).order_by('service__name')
        shipment_services_size = len(shipment_services)
        for shipment_service in shipment_services:
            shipment_services_json.append({'service_id': shipment_service.service_id,
                                           'service_price': str(shipment_service.price),
                                           'service_quantity': str(shipment_service.quantity)})
    elif has_shipment_perm(request.user, 'add_shipmentservice') is False:
        return HttpResponseForbidden()
    else:
        selected_services = request.POST.getlist('service')
        shipment_services_size = len(selected_services)
        logger.debug(selected_services)
        shipment = Shipment.objects.get(id=sid)
        ShipmentService.objects.filter(shipment_id=sid).delete()
        for selected_service in selected_services:
            service_price = request.POST.get('price' + selected_service)
            service_quantity = request.POST.get('quantity' + selected_service)
            logger.debug(service_price)
            shipment_service = ShipmentService.objects.bulk_create([
                ShipmentService(shipment_id=sid, service_id=selected_service, price=service_price,
                                quantity=service_quantity)
            ])
            shipment_services_json.append({'service_id': shipment_service[0].id,
                                           'service_name': Service.objects.filter(pk=selected_service)[0].name,
                                           'service_price': str(service_price),
                                           'service_quantity': str(service_quantity)})
        shipment_products = shipment.product_set.all()
        ignore_http_response, cost = calculate_shipment(shipment, shipment_products, shipment.user_id)
        logger.debug(cost)
    return HttpResponse(json.dumps({'new_cost': force_text(formats.number_format(round(cost, 2), use_l10n=True,
                                                                                 decimal_pos=2)),
                                    'new_cost_raw': round(cost, 2),
                                    'shipment_services': shipment_services_json, 'v': shipment_services_size}),
                        content_type='application/json')
