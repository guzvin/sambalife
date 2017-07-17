from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from utils.models import Params, Accounting, AccountingPartner
from partner.models import Partner
import logging

logger = logging.getLogger('django')


class ParamsAdmin(admin.ModelAdmin):
    list_display = ('translated_name',)

    fieldsets = (
        (None, {
            'fields': [
                'amazon_fee', 'shipping_cost', 'partner_cost'
            ]
        }),
        (_('Redirecionamento'), {
            'description': _('Configuração do redirecionamento.'),
            'fields': [
                'redirect_factor', 'time_period_one', 'redirect_factor_two',
                'time_period_two', 'redirect_factor_three', 'time_period_three'
            ]
        }),
    )

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


class AccountingPartnerInline(admin.TabularInline):
    model = AccountingPartner
    readonly_fields = ('partner_lookup_name', 'value', 'total_products',)
    exclude = ('partner',)
    can_delete = False
    max_num = 0
    verbose_name = _('Fechamento por Parceiro')
    verbose_name_plural = _('Fechamento por Parceiro')

    def partner_lookup_name(self, obj):
        try:
            partner = Partner.objects.get(identity=obj.partner)
            return partner.name
        except Partner.DoesNotExist:
            return 'Fábio/Gustavo/Roberto'

    partner_lookup_name.short_description = _('Parceiro')


class AccountingAdmin(admin.ModelAdmin):
    list_display = ('date',)
    readonly_fields = ('date', 'user', 'ipaddress',)

    inlines = [
        AccountingPartnerInline,
    ]

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(AccountingAdmin, self).has_module_permission(request)
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(AccountingAdmin, self).has_delete_permission(request, obj)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_authenticated and request.user.first_name == 'Administrador':
            return super(AccountingAdmin, self).has_change_permission(request, obj)
        return False


admin.site.register(Accounting, AccountingAdmin)
