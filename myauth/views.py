from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth import login
from django.utils.translation import ugettext as _

import logging

logger = logging.getLogger('django')


@login_required
@require_http_methods(["GET", "POST"])
def user_edit(request):
    if request.user.first_name == 'Administrador':
        return HttpResponseForbidden()
    user_model = get_user_model()
    UserFormSet = modelformset_factory(user_model, fields=('first_name', 'last_name', 'email', 'phone',
                                                           'cell_phone'), min_num=1, max_num=1)
    context_data = {}
    if request.method == 'GET':
        user_formset = UserFormSet(queryset=user_model.objects.filter(pk=request.user.pk))
        if request.GET.get('s') == '1':
            context_data['success'] = True
            context_data['success_message'] = _('Alteração salva com sucesso.')
    else:
        user_formset = UserFormSet(request.POST)
        if user_formset.is_valid():
            user_formset.save()
            return HttpResponseRedirect('%s?s=1' % reverse('user_edit'))
    context_data['user_formset'] = user_formset
    return render(request, 'user_edit.html', context_data)


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
