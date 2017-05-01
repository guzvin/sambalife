from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from shipment.models import CostFormula
import logging

logger = logging.getLogger('django')


class CostFormulaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(CostFormulaForm, self).__init__(*args, **kwargs)
        self.fields['formula'].label = _('Fórmula*')

    class Meta:
        model = CostFormula
        fields = ('formula',)


class CostFormulaAdmin(admin.ModelAdmin):
    form = CostFormulaForm

    list_display = ('translated_name',)

    def translated_name(self, obj):
        return _('Fórmula')

    translated_name.short_description = _('Cálculo de Envio')

    def has_module_permission(self, request):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(CostFormulaAdmin, self).has_module_permission(request)
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(CostFormulaAdmin, self).has_delete_permission(request, obj)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(CostFormulaAdmin, self).has_change_permission(request, obj)
        return False

    def has_add_permission(self, request):
        if request.user.is_authenticated:
            formula_exists = CostFormula.objects.all().count() == 1
            if request.user.first_name == 'Administrador' and formula_exists is False:
                return super(CostFormulaAdmin, self).has_add_permission(request)
        return False

admin.site.register(CostFormula, CostFormulaAdmin)
