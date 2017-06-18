from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from utils.models import Params
import logging

logger = logging.getLogger('django')


class ParamsAdmin(admin.ModelAdmin):
    list_display = ('translated_name',)

    def translated_name(self, obj):
        return _('Parâmetros')

    translated_name.short_description = _('Parametrizações')

    def has_module_permission(self, request):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(ParamsAdmin, self).has_module_permission(request)
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(ParamsAdmin, self).has_delete_permission(request, obj)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(ParamsAdmin, self).has_change_permission(request, obj)
        return False

    def has_add_permission(self, request):
        if request.user.is_authenticated:
            formula_exists = Params.objects.all().count() == 1
            if request.user.first_name == 'Administrador' and formula_exists is False:
                return super(ParamsAdmin, self).has_add_permission(request)
        return False

admin.site.register(Params, ParamsAdmin)
