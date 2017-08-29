from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login

import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET", "POST"])
def user_edit(request, pid=None):
    user_model = get_user_model()
    UserFormSet = modelformset_factory(user_model, fields=('first_name', 'last_name', 'phone',
                                                           'cell_phone'), min_num=1, max_num=1)
    user_formset = UserFormSet(queryset=user_model.objects.filter(pk=request.user.pk))
    return render(request, 'user_edit.html', {'user_formset': user_formset})


@login_required
@require_http_methods(["POST"])
def user_impersonate(request):
    if request.user.is_superuser:
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=request.POST.get('impersonate_id'))
            original_user_id = request.user.id
            login(request, user)
            request.session['impersonated'] = original_user_id
        except user_model.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse('product_stock'))


@login_required
@require_http_methods(["GET"])
def user_end_impersonate(request):
    original_user_id = request.session['impersonated']
    if original_user_id is not None:
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=original_user_id)
            del request.session['impersonated']
            login(request, user)
        except user_model.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse('product_stock'))
