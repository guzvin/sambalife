from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseForbidden
from service.models import Product
from service.templatetags.services import has_service_perm
import json
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET", "POST"])
def service_product(request, pid=None):
    if has_service_perm(request.user, 'add_product') is False:
        return HttpResponseForbidden()
    services_product_json = []
    if request.method == 'GET':
        services_product = Product.objects.filter(product_id=pid).order_by('service__name')
        for _service_product in services_product:
            services_product_json.append({'service_id': _service_product.service_id,
                                          'service_price': str(_service_product.price)})
    else:
        selected_services = request.POST.getlist('service')
        logger.debug(selected_services)
        Product.objects.filter(product_id=pid).delete()
        for selected_service in selected_services:
            service_price = request.POST.get('price' + selected_service)
            logger.debug(service_price)
            Product.objects.bulk_create([
                Product(product_id=pid, service_id=selected_service, price=service_price)
            ])
    return HttpResponse(json.dumps(services_product_json), content_type='application/json')
