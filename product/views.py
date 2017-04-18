from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db import transaction
from product.forms import ProductForm
from product.models import Product, Tracking
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, QueryDict, HttpResponseRedirect
from django.utils import formats
from product.templatetags.products import has_product_perm
from myauth.templatetags.users import has_user_perm
import json
import logging

logger = logging.getLogger('django')


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


@login_required
@require_http_methods(["GET"])
def product_stock(request):
    if has_product_perm(request.user, 'view_products'):
        is_user_perm = has_user_perm(request.user, 'view_users')
        queries = []
        logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        filter_id = request.GET.get('id')
        logger.debug(str(filter_id))
        filter_name = request.GET.get('name')
        logger.debug(str(filter_name))
        filter_user = request.GET.get('user')
        logger.debug(str(filter_user))
        filter_status = request.GET.get('status')
        logger.debug(str(filter_status))
        filter_values = {
            'status': '',
        }
        if filter_id:
            queries.append(Q(pk__startswith=filter_id))
            filter_values['id'] = filter_id
        if filter_name:
            queries.append(Q(name__icontains=filter_name))
            filter_values['name'] = filter_name
        if is_user_perm and filter_user:
            queries.append(Q(user__first_name__icontains=filter_user) | Q(user__last_name__icontains=filter_user))
            filter_values['user'] = filter_user
        if filter_status:
            queries.append(Q(status=filter_status))
            filter_values['status'] = filter_status
        logger.debug(str(queries))
        logger.debug(str(len(queries)))
        is_filtered = len(queries) > 0
        if is_filtered:
            query = queries.pop()
            for item in queries:
                query &= item
            logger.debug(str(query))
        if is_user_perm:
            if is_filtered:
                logger.debug('FILTERED')
                products_list = Product.objects.filter(query).select_related('user')
            else:
                logger.debug('ALL')
                products_list = Product.objects.all().select_related('user')
        else:
            query &= Q(user=request.user)
            products_list = Product.objects.filter(query)
    else:
        products_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(products_list, 10)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, 'product_stock.html', {'title': _('Estoque'), 'products': products,
                                                  'filter_values': ObjectView(filter_values)})


@login_required
def product_add(request):
    if request.method != 'POST':
        return render(request, 'product_add.html', {'title': _('Produto')})
    else:
        form = ProductForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product = Product()
                product.name = form.cleaned_data.get('name')
                product.description = form.cleaned_data.get('description')
                product.quantity = form.cleaned_data.get('quantity')
                product.send_date = form.cleaned_data.get('send_date')
                product.user = request.user
                product.save()
                tracking_numbers_list = request.POST.getlist('track_number')
                for tracking_number in tracking_numbers_list:
                    tracking = Tracking()
                    tracking.track_number = tracking_number
                    tracking.product = product
                    tracking.save()
            return render(request, 'product_add.html', {'title': _('Produto'), 'success': True,
                                                        'success_message': _('Produto inserido com sucesso.')})
        return render(request, 'product_add.html', {'title': _('Produto'), 'success': False, 'form': form})


@login_required
@require_http_methods(["PUT"])
def product_edit(request, pid=None, output=None):
    if has_product_perm(request.user, 'change_product_status'):
        request.PUT = QueryDict(request.body)
        try:
            product = Product.objects.select_related('user').get(pk=pid)
            if product.user == request.user or has_user_perm(request.user, 'view_users'):
                fields_to_update = []
                product_status = request.PUT.get('product_status')
                product_status_display = None
                if product_status:
                    for choice in Product.STATUS_CHOICES:
                        if str(choice[0]) == product_status:
                            product.status = product_status
                            product_status_display = str(choice[1])
                            break
                    if product_status_display is not None:
                        fields_to_update.append('status')
                if len(fields_to_update) == 0:
                    raise Product.DoesNotExist
                product.save(update_fields=fields_to_update)
                if output and output == 'json':
                    product_json = {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description,
                        'quantity': product.quantity,
                        'send_date': formats.date_format(product.send_date, "DATE_FORMAT"),
                        'status': product.status,
                        'status_display': product_status_display,
                    }
                    return HttpResponse(json.dumps({'success': True, 'product': product_json}),
                                        content_type='application/json')
                else:
                    pass  # TODO retorno de sucesso da edição HTML
        except Product.DoesNotExist:
            if output and output == 'json':
                return HttpResponse(json.dumps({'success': False}),
                                    content_type='application/json', status=400)
            else:
                pass  # TODO retorno de erro da edição HTML
    if output and output == 'json':
        return HttpResponse(json.dumps({'success': False}),
                            content_type='application/json', status=403)
    else:
        pass  # TODO retorno de erro da edição HTML


@login_required
@require_http_methods(["GET"])
def product_details(request, pid=None):
    if has_product_perm(request.user, 'view_products'):
        query = Q(pk=pid)
        try:
            if has_user_perm(request.user, 'view_users') is False:
                query &= Q(user=request.user)
                product = Product.objects.get(query)
            else:
                product = Product.objects.select_related('user').get(query)
            product_tracking = Tracking.objects.filter(product=product)
            return render(request, 'product_details.html', {'title': _('Produto'), 'product': product,
                                                            'product_tracking': product_tracking})
        except Product.DoesNotExist:
            pass
    return render(request, 'product_details.html', {'title': _('Produto')})


@login_required
@require_http_methods(["POST"])
def product_delete(request):
    if has_product_perm(request.user, 'delete_product'):
        request.DELETE = QueryDict(request.body)
        query = Q(pk=request.DELETE.get('pid'))
        if has_user_perm(request.user, 'view_users') is False:
            query &= Q(user=request.user)
        Product.objects.filter(query).delete()
    return HttpResponseRedirect('/product/stock/')
