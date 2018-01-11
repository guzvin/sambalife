from django import forms
from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter, SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from store.models import Lot, Product, Config, LotReport
from utils import helper
from utils.models import Params
from utils.sites import admin_site
from utils.middleware.thread_local import get_current_request
from service.models import Service
from django.contrib.admin import utils
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.main import ChangeList
from rangefilter.filter import DateRangeFilter
import logging

logger = logging.getLogger('django')


class GroupModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if obj.name == 'all_users':
            return str(_('Todos usuários'))
        if obj.name == 'admins':
            return str(_('Administradores do sistema'))
        return obj.name


class ServiceModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name + ' - ' + str(obj.price)


class LotForm(forms.ModelForm):
    groups = GroupModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Grupos'), False),
        label=_('Grupos'),
        help_text=_('Grupos aos quais este lote pertence. Deixe em branco para não restringir o acesso à ele.')
    )

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(LotForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            # Populate the groups field with the current Groups.
            self.fields['groups'].initial = self.instance.groups.all()
        else:
            config = Config.objects.first()
            if config:
                logger.info('################ DEFAULT GROUP #################')
                # logger.info(config.default_group)
                self.fields['groups'].initial = [config.default_group]

    class Meta:
        model = Lot
        exclude = []

    def save(self, *args, **kwargs):
        logger.debug('@@@@@@@@@@@@@@@ LOT SAVE @@@@@@@@@@@@@@@@@')
        instance = super(LotForm, self).save(commit=False)
        if instance.pk is None:
            instance.save()
        instance.groups = self.cleaned_data['groups']

        instance.save()
        return instance


class LotProductForm(forms.ModelForm):
    redirect_services = ServiceModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=True,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Serviços'), False),
        label=_('Serviços'),
        help_text=_('Serviços utilizados na preparação do envio.')
    )

    class Meta:
        model = Product
        fields = ('name', 'identifier', 'url', 'buy_price', 'sell_price', 'rank', 'quantity', 'fba_fee', 'amazon_fee',
                  'shipping_cost', 'redirect_services', 'condition', 'voi_value')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(LotProductForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            params = Params.objects.first()
            if params:
                self.fields['amazon_fee'].initial = params.amazon_fee
                self.fields['shipping_cost'].initial = params.shipping_cost
        else:
            # Populate the redirect_services field with the current Services.
            self.fields['redirect_services'].initial = self.instance.redirect_services.all()
        # self.fields['condition'].required = True

    def save(self, *args, **kwargs):
        instance = super(LotProductForm, self).save(commit=False)
        if instance.pk is None:
            instance.save()
        redirect_cost = 0
        instance.redirect_services = self.cleaned_data['redirect_services']
        logger.debug('@@@@@@@@@@@@@ REDIRECT COST @@@@@@@@@@@@@@@@')
        logger.debug(instance.redirect_services)
        for redirect_service in instance.redirect_services.all():
            logger.debug(redirect_service.price)
            redirect_cost += redirect_service.price
        logger.debug(redirect_cost)
        instance.product_cost = instance.buy_price + instance.amazon_fee + instance.fba_fee + instance.shipping_cost + \
            redirect_cost
        instance.profit_per_unit = instance.sell_price - instance.product_cost
        instance.total_profit = instance.profit_per_unit * instance.quantity
        instance.roi = (instance.profit_per_unit / instance.product_cost) * 100
        instance.save()
        return instance


class LotProductInline(admin.StackedInline):
    model = Product
    formset = helper.RequiredBaseInlineFormSet
    form = LotProductForm
    can_delete = True
    extra = 1
    verbose_name = _('Produto')
    verbose_name_plural = _('Produtos')

    def get_extra(self, request, obj=None, **kwargs):
        return self.extra if obj is None else 0


class LotAdmin(admin.ModelAdmin):
    form = LotForm

    inlines = [
        LotProductInline,
    ]

    list_filter = [
        'status',
        ('create_date', DateFieldListFilter),
    ]

    search_fields = ('name', 'product__name',)
    list_display_links = ('id', 'name',)
    list_display = ('id', 'name', 'create_date', 'products_quantity', 'status', 'lot_cost')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'thumbnail', 'groups')}),
    )

    def save_related(self, request, form, formsets, change):
        products_quantity = 0
        products_cost = 0
        profit = 0
        average_rank = 0
        lot_cost = 0
        redirect_cost = 0
        related_changed = False
        form.save_m2m()
        for formset in formsets:
            products = formset.save()
            related_changed = len(products) > 0
        if related_changed:
            lot = form.save(commit=False)
            products = Product.objects.filter(lot=lot)
            for product in products:
                product_redirect_cost = 0
                for redirect_service in product.redirect_services.all():
                    product_redirect_cost += redirect_service.price
                products_quantity += product.quantity
                products_cost += product.product_cost * product.quantity
                profit += product.total_profit
                average_rank += (product.rank / 100)
                lot_cost += ((product.buy_price + product_redirect_cost) * product.quantity)
                redirect_cost += (product_redirect_cost * product.quantity)
            lot.products_quantity = products_quantity
            lot.products_cost = products_cost
            lot.profit = profit
            lot.average_roi = (profit / products_cost) * 100
            lot.average_rank = (average_rank / len(products)) * 100
            lot.lot_cost = lot_cost
            lot.redirect_cost = redirect_cost
            lot.save()
            if not change:
                config = Config.objects.first()
                if config:
                    logger.info('@@@@@@@@@@@@@@@@@@@@@@@@@ ENVIAR EMAIL ASSINANTES @@@@@@@@@@@@@@@@@@@@@@@')
                    users = get_user_model().objects.filter(groups=config.default_group)
                    LotAdmin.email_users_new_lot(get_current_request(), lot, users)

    @staticmethod
    def email_users_new_lot(request, lot, users):
        emails = ()
        for user in users:
            emails += (LotAdmin.assemble_email_new_lot(request, lot, user),)
        if emails:
            helper.send_email(emails, bcc_admins=True, async=True)

    @staticmethod
    def assemble_email_new_lot(request, lot, user):
        email_title = _('Novo lote cadastrado no sistema \'%(lot)s\'') % {'lot': lot.name}
        html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'] +
                              ['<br>{}'] * 5 +
                              ['</p>'] +
                              ['<p><a href="{}">{}</a> {}</p>'])
        texts = (_('Lote %(lot_name)s') % {'lot_name': lot.name},
                 _('Valor: U$ %(lot_cost)s') % {'lot_cost': helper.force_text(helper.formats.
                                                                              number_format(lot.lot_cost,
                                                                                            use_l10n=True,
                                                                                            decimal_pos=2))},
                 _('Lucro: U$ %(lot_profit)s') % {'lot_profit': helper.force_text(helper.formats.
                                                                                  number_format(lot.profit,
                                                                                                use_l10n=True,
                                                                                                decimal_pos=2))},
                 _('Número de itens: %(lot_items)s') % {'lot_items': lot.products_quantity},
                 _('ROI médio: %(lot_roi)s%%') % {'lot_roi': helper.force_text(helper.formats.
                                                                         number_format(lot.average_roi,
                                                                                       use_l10n=True,
                                                                                       decimal_pos=2))},
                 _('Rank médio: %(lot_rank)s%%') % {'lot_rank': lot.average_rank})
        texts += (''.join(['https://', request.CURRENT_DOMAIN, helper.reverse('store_lot_details', args=[lot.id])]),
                  _('Clique aqui'), _('para acessar este lote agora mesmo!'),)
        email_body = helper.format_html(html_format, *texts)
        return helper.build_basic_template_email_tuple(request, user.first_name, [user.email], email_title,
                                                       email_body)

admin_site.register(Lot, LotAdmin)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('translated_name',)

    def translated_name(self, obj):
        return _('Configuração')

    translated_name.short_description = _('Configuração')

    def has_add_permission(self, request):
        if request.user.is_authenticated:
            config_exists = Config.objects.all().count() == 1
            if config_exists is False:
                return super(ConfigAdmin, self).has_add_permission(request)
        return False

admin_site.register(Config, ConfigAdmin)


class LotReportChangeList(ChangeList):
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable, model_admin):
        super(LotReportChangeList, self).__init__(request, model, list_display, list_display_links,
                                                  list_filter, date_hierarchy, search_fields, list_select_related,
                                                  list_per_page, list_max_show_all, list_editable, model_admin)
        self.title = _('Relatório de Lotes')


class LotReportForm(forms.ModelForm):
    class Meta:
        model = LotReport
        exclude = []
        translation_from_date, translation_to_date = _('From date'), _('To date')


class LotReportAdmin(admin.ModelAdmin):
    form = LotReportForm

    list_display_links = None
    list_filter = [
        'status',
        ('create_date', DateRangeFilter),
        ('sell_date', DateRangeFilter),
    ]

    search_fields = ('name', 'product__name',)
    list_display = ('id', 'name', 'create_date', 'products_quantity', 'status', 'lot_cost')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def get_changelist(self, request, **kwargs):
        return LotReportChangeList

admin_site.register(LotReport, LotReportAdmin)


native_lookup_field = utils.lookup_field


def my_lookup_field(name, obj, model_admin=None):
    if name == 'action_checkbox' and ((str(model_admin) == 'store.LotAdmin' and obj.status == 2) or
                                      str(model_admin) == 'store.LotReportAdmin'):
        raise ObjectDoesNotExist
    return native_lookup_field(name, obj, model_admin=model_admin)

utils.lookup_field = my_lookup_field
