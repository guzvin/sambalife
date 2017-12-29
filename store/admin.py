from django import forms
from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from store.models import Lot, Product, Config
from utils import helper
from utils.models import Params
from utils.sites import admin_site
from utils.middleware.thread_local import get_current_request
from django.contrib.admin import utils
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger('django')


class GroupModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if obj.name == 'all_users':
            return str(_('Todos usuários'))
        if obj.name == 'admins':
            return str(_('Administradores do sistema'))
        return obj.name


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
    class Meta:
        model = Product
        fields = ('name', 'identifier', 'url', 'buy_price', 'sell_price', 'quantity', 'fba_fee', 'amazon_fee',
                  'shipping_cost')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(LotProductForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            params = Params.objects.first()
            if params:
                self.fields['amazon_fee'].initial = params.amazon_fee
                self.fields['shipping_cost'].initial = params.shipping_cost

    def save(self, *args, **kwargs):
        instance = super(LotProductForm, self).save(commit=False)
        params = Params.objects.first()
        if params:
            instance.redirect_factor = params.redirect_factor
        instance.product_cost = instance.buy_price + instance.amazon_fee + instance.fba_fee + instance.shipping_cost + \
            instance.redirect_factor
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
        (None, {'fields': ('name', 'description', 'thumbnail', 'groups', 'rank')}),
    )

    def save_related(self, request, form, formsets, change):
        products_quantity = 0
        products_cost = 0
        profit = 0
        average_roi = 0
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
                products_quantity += product.quantity
                products_cost += product.product_cost * product.quantity
                profit += product.total_profit
                average_roi += (product.roi / 100)
                lot_cost += (product.buy_price * product.quantity)
                redirect_cost += (product.redirect_factor * product.quantity)
            lot.products_quantity = products_quantity
            lot.products_cost = products_cost
            lot.profit = profit
            lot.average_roi = (average_roi / len(products)) * 100
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
                              ['<br>{}'] * 4 +
                              ['</p>'] +
                              ['<p><a href="{}">{}</a> {}</p>'])
        texts = (_('Lote %(lot_name)s') % {'lot_name': lot.name},
                 _('Valor: U$ %(lot_cost)s') % {'lot_cost': helper.force_text(helper.formats.
                                                                              number_format(lot.lot_cost,
                                                                                            use_l10n=True,
                                                                                            decimal_pos=2))},
                 _('Número de itens: %(lot_items)s') % {'lot_items': lot.products_quantity},
                 _('ROI: %(lot_roi)s%%') % {'lot_roi': helper.force_text(helper.formats.
                                                                         number_format(lot.average_roi,
                                                                                       use_l10n=True,
                                                                                       decimal_pos=2))},
                 _('Rank: %(lot_rank)s%%') % {'lot_rank': lot.rank})
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

native_lookup_field = utils.lookup_field


def my_lookup_field(name, obj, model_admin=None):
    if name == 'action_checkbox' and str(model_admin) == 'store.LotAdmin' and obj.status == 2:
        raise ObjectDoesNotExist
    return native_lookup_field(name, obj, model_admin=model_admin)

utils.lookup_field = my_lookup_field
