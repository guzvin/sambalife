from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth import get_user_model
from django.http import HttpResponse, QueryDict, HttpResponseRedirect, HttpResponseForbidden

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
