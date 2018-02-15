from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from utils.models import Params, Accounting, AccountingPartner
from utils.sites import admin_site
from utils.views import close_accounting
from partner.models import Partner
import logging

logger = logging.getLogger('django')


class ParamsAdmin(admin.ModelAdmin):
    list_display = ('translated_name',)

    fieldsets = (
        (None, {
            'fields': [
                'amazon_fee', 'shipping_cost', 'fgr_cost', 'contact_us_mail_to'
            ]
        }),
        # (_('Redirecionamento'), {
        #     'description': _('Configuração do redirecionamento.'),
        #     'fields': [
        #         'redirect_factor', 'time_period_one', 'redirect_factor_two',
        #         'time_period_two', 'redirect_factor_three', 'time_period_three'
        #     ]
        # }),
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

admin_site.register(Params, ParamsAdmin)


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
            return _('Repasse')

    partner_lookup_name.short_description = _('Parceiro')


class AccountingAdmin(admin.ModelAdmin):
    list_display = ('date',)
    readonly_fields = ('date', 'user', 'ipaddress',)
    fieldsets = (
        (None, {'fields': ('date', 'user', 'ipaddress',)}),
    )

    inlines = [
        AccountingPartnerInline,
    ]

    simulate_obj = None
    simulate_inlines = None

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

    def get_object(self, request, object_id, from_field=None):
        if object_id == 'simulate' or object_id == 'simulate_sandbox':
            self.simulate_obj, self.simulate_inlines = close_accounting(request, True, object_id == 'simulate_sandbox')
            self.simulate_obj.simulation = True
            return self.simulate_obj
        else:
            return super(AccountingAdmin, self).get_object(request, object_id, from_field)

    def get_inline_instances(self, request, obj=None):
        inline_instances = super(AccountingAdmin, self).get_inline_instances(request, obj)
        if obj and obj.simulation:
            for idx, inline in enumerate(inline_instances):
                inline.extra = len(self.simulate_inlines)
                inline.max_num = len(self.simulate_inlines)
                inline_instances[idx] = inline
        return inline_instances

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        inline_admin_formsets = super(AccountingAdmin, self).get_inline_formsets(request, formsets, inline_instances,
                                                                                 obj)
        if obj and obj.simulation:
            for inline_admin_formset in inline_admin_formsets:
                for form, data in zip(inline_admin_formset.formset.forms, self.simulate_inlines):
                    form.instance = data
        return inline_admin_formsets

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.simulation:
            context['title'] = _('Simulação Fechamento')
        return super(AccountingAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def get_queryset(self, request):
        qs = super(AccountingAdmin, self).get_queryset(request)
        qs = qs.filter(is_sandbox=False)
        return qs


admin_site.register(Accounting, AccountingAdmin)
