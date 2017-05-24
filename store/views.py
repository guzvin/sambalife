from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET"])
def store_list(request):
    return render(request, 'store_list.html')


@login_required
@require_http_methods(["GET", "POST"])
def store_lot_add(request):
    return render(request, 'store_lot_add.html')


@login_required
@require_http_methods(["GET"])
def store_lot_details(request, pid=None):
    return render(request, 'store_lot_details.html')


def store_admin(request):
    return render(request, 'store_admin.html')


def store_purchase(request):
    return render(request, 'store_purchase.html')
