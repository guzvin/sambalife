from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.admin.options import TO_FIELD_VAR
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.contrib.auth import get_user_model
from store.models import Lot, Product, Config, LotReport, lot_directory_path, Collaborator
from store.admin_filters import UserFilter, AsinFilter
from utils import helper
from utils.models import Params
from utils.sites import admin_site
from utils.middleware.thread_local import get_current_request
from service.models import Service
from django.contrib.admin import utils
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.main import ChangeList
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.contrib.admin.utils import quote, unquote
from shutil import copy2
from django.conf import settings
from rangefilter.filter import DateRangeFilter
import os
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
        instance.roi = (instance.profit_per_unit / (instance.buy_price + redirect_cost)) * 100
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

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = ['vendor/jquery/jquery%s.js' % extra, 'jquery.init.js']
        if self.filter_vertical or self.filter_horizontal:
            js.extend(['SelectBox.js', 'SelectFilter2.js'])
        if self.classes and 'collapse' in self.classes:
            js.append('collapse%s.js' % extra)
        js = ['admin/js/%s' % url for url in js]
        js.append('js/specifics/store_inlines.js')
        return forms.Media(js=js)


class LotAdmin(admin.ModelAdmin):
    form = LotForm

    inlines = [
        LotProductInline,
    ]

    list_filter = [
        'is_archived',
        'status',
        'is_fake',
        ('create_date', DateRangeFilter),
        ('sell_date', DateRangeFilter),
    ]

    search_fields = ('name', 'product__name', 'product__identifier',)
    list_display_links = ('id', 'name',)
    list_display = ('id', 'name', 'create_date', 'products_quantity', 'status', 'lot_cost', 'sell_date', 'is_archived',
                    'is_fake', 'duplicate_lot_action')
    fieldsets = (
        (None, {'fields': ('is_fake', 'is_archived', 'status', 'sell_date', 'payment_complete', 'name', 'order_weight',
                           'description', 'collaborator', 'thumbnail', 'groups')}),
    )

    def duplicate_lot_action(self, obj):
        return format_html('<a class="button" href="{}">{}</a>', reverse('admin:duplicate_lot',
                                                                         args=[obj.pk]), _('Duplicar lote'))
    duplicate_lot_action.short_description = _('Duplicar')
    duplicate_lot_action.allow_tags = True

    def save_form(self, request, form, change):
        lot_obj = super(LotAdmin, self).save_form(request, form, change)
        if request.method == 'POST':
            request.POST['_lot_obj'] = lot_obj
        return lot_obj

    def save_related(self, request, form, formsets, change):
        products_quantity = 0
        products_cost = 0
        profit = 0
        average_rank = 0
        lot_cost = 0
        redirect_cost = 0
        voi_cost = 0
        related_changed = False
        # logger.debug('@@@@@@@@@@@@@@@@@@@ LOT CHANGED FIELDS LOT CHANGED FIELDS @@@@@@@@@@@@@@@@@@@@@@@@@@')
        # lot_changes = {}
        is_archived_changed = False
        form_changed_data = form.changed_data
        if form_changed_data:
            for field_changed in form_changed_data:
                is_archived_changed = field_changed == 'is_archived'
                if is_archived_changed:
                    break
        #         lot_changes['lot'][field_changed] = form.cleaned_data[field_changed]
        logger.debug('@@@@@@@@@@@@@@@@@@@ LOT ARCHIVED CHANGED LOT ARCHIVED CHANGED @@@@@@@@@@@@@@@@@@@@@@@@@@')
        logger.debug(is_archived_changed)
        logger.debug(change)
        form.save_m2m()
        for formset in formsets:
            _deleted_forms = formset.deleted_forms
            logger.debug('@@@@@@@@@@@@@@@@@@ DELETED OBJECTS @@@@@@@@@@@@@@@@@@@@@@')
            logger.debug(_deleted_forms)
            products = formset.save()
            related_changed = len(products) > 0 or len(_deleted_forms) > 0
            if related_changed:
                break
            # logger.debug('@@@@@@@@@@@@@@@@@@@ PRODUCT CHANGED FIELDS PRODUCT CHANGED FIELDS @@@@@@@@@@@@@@@@@@@@@@@@')
            # for product_form in formset.forms:
            #     product_form_changed_data = product_form.changed_data
            #     if product_form_changed_data:
            #         if 'products' not in lot_changes:
            #             lot_changes['products'] = []
            #         # for field_changed in form_changed_data:
            #         lot_changes['products'].append({
            #             product_form.cleaned_data['name']: product_form_changed_data
            #         })
            #     logger.debug(lot_changes)
        lot = request.POST.get('_lot_obj', form.save(commit=False))
        if related_changed:
            products = Product.objects.filter(lot=lot)
            logger.debug('@@@@@@@@@@@@@@@@@@ RELATED QUERY RELATED QUERY RELATED QUERY @@@@@@@@@@@@@@@@@@@@@@')
            logger.debug(len(products))
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
                voi_cost += product.voi_value * product.quantity
            lot.products_quantity = products_quantity
            lot.products_cost = products_cost
            lot.profit = profit
            lot.average_roi = (profit / lot_cost) * 100
            lot.average_rank = (average_rank / len(products)) * 100
            lot.lot_cost = lot_cost
            lot.redirect_cost = redirect_cost
            lot.voi_cost = voi_cost
            lot.voi_profit = lot.lot_cost - lot.voi_cost
            lot.voi_roi = (lot.voi_profit / lot.voi_cost) * 100 if lot.voi_cost > 0 else 0
            lot.save()
        logger.debug(lot.is_fake)
        logger.debug(lot.is_archived)
        if lot.is_fake is False and lot.is_archived is False:
            if change is False or change and is_archived_changed:
                lot_groups = lot.groups.all()
                users = []
                for lot_group in lot_groups:
                    users += get_user_model().objects.filter(groups=lot_group)
                if users:
                    logger.debug(users)
                    logger.debug('@@@@@@@@@@@@@@@ NEW LOT USERS NEW LOT USERS NEW LOT USERS @@@@@@@@@@@@@@@@@@')
                    LotAdmin.email_users_new_lot(get_current_request(), lot, users)

    @staticmethod
    def email_users_new_lot(request, lot, users):
        emails = ()
        for user in users:
            emails += (LotAdmin.assemble_email_new_lot(request, lot, user),)
        if emails:
            helper.send_email(emails, bcc_admins=False, async=True)

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

    @staticmethod
    def email_users_lot_changed(request, lot, users):
        emails = ()
        for user in users:
            emails += (LotAdmin.assemble_email_lot_changed(request, lot, user),)
        if emails:
            helper.send_email(emails, bcc_admins=True, async=True)

    @staticmethod
    def assemble_email_lot_changed(request, lot, user):
        email_title = _('Lote alterado \'%(lot)s\'') % {'lot': lot.name}
        html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                              ['<p><a href="{}">{}</a> {}</p>'])
        texts = (_('Este lote sofreu alterações.'),)
        texts += (''.join(['https://', request.CURRENT_DOMAIN, helper.reverse('store_lot_details', args=[lot.id])]),
                  _('Clique aqui'), _('para visualizá-las.'),)
        email_body = helper.format_html(html_format, *texts)
        return helper.build_basic_template_email_tuple(request, user.first_name, [user.email], email_title,
                                                       email_body)

    def get_urls(self):
        from django.conf.urls import url
        urls = super().get_urls()
        custom_url = [url(r'^duplicate_lot/(?P<lid>.+)[/]$', self.admin_site.admin_view(self.duplicate_lot),
                          name='duplicate_lot')]
        return custom_url + urls

    def duplicate_lot(self, request, lid):
        logger.debug('@@@@@@@@@@@@@@@  DUPLICATE LOT DUPLICATE LOT DUPLICATE LOT @@@@@@@@@@@@@@@@@@@@@@')
        logger.debug(lid)
        context = {
            'my_show_save_as': True,
            'show_save': False,
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'show_delete_link': False,
            'show_delete': False
                   }
        request.GET = request.GET.copy()
        request.GET['duplicate_lot'] = True
        return self.changeform_view(request, lid, '', context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        logger.debug('@@@@@@@@@@@@@@ DUP LOTE DUP LOTE DUP LOTE @@@@@@@@@@@@@@@@')
        if request.method == 'POST':
            new_thumbnail = request.FILES.get('thumbnail', None)
            logger.debug('@@@@@@@@@@@@@@ NEW THUMBNAIL @@@@@@@@@@@@@@@@')
            logger.debug(new_thumbnail)
            if object_id and new_thumbnail is None:
                to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
                obj = self.get_object(request, unquote(object_id), to_field)
                logger.debug('@@@@@@@@@@@@@@ OLD THUMBNAIL @@@@@@@@@@@@@@@@')
                logger.debug(obj.thumbnail)
                request.POST['_my_obj_thumbnail'] = str(obj.thumbnail)
        self.save_as = extra_context.get('my_show_save_as', False) if extra_context else False
        return super(LotAdmin, self).changeform_view(request, object_id, form_url, extra_context)

    def get_object(self, request, object_id, from_field=None):
        obj = super(LotAdmin, self).get_object(request, object_id, from_field)
        if request.GET.get('duplicate_lot', False):
            obj.status = 1
            obj.sell_date = None
            obj.payment_complete = False
        return obj

    def response_add(self, request, obj, post_url_continue=None):
        obj_thumbnail = request.POST.get('_my_obj_thumbnail', None)
        if obj_thumbnail:
            dir_name, file_name = os.path.split(obj_thumbnail)
            file_path = lot_directory_path(obj, file_name)
            obj.thumbnail = file_path
            dir_name, file_name = os.path.split(file_path)
            dir_name = os.path.join(settings.MEDIA_ROOT, dir_name)
            os.makedirs(dir_name)
            copy2(os.path.join(settings.MEDIA_ROOT, obj_thumbnail), dir_name)
            obj.save()
        return super(LotAdmin, self).response_add(request, obj, post_url_continue)

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'admin/js/core.js',
            'admin/js/vendor/jquery/jquery%s.js' % extra,
            'externo/jquery/jquery-ui.min.js',
            'admin/js/jquery.init.js',
            'admin/js/admin/RelatedObjectLookups.js',
            'admin/js/actions%s.js' % extra,
            'admin/js/urlify.js',
            'admin/js/prepopulate%s.js' % extra,
            'admin/js/vendor/xregexp/xregexp%s.js' % extra,
        ]
        return forms.Media(js=js)

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
        self.lot_cost_sum = None
        self.voi_cost_sum = None
        self.voi_profit_sum = None
        self.voi_roi_sum = None
        self.products_quantity_sum = None
        super(LotReportChangeList, self).__init__(request, model, list_display, list_display_links,
                                                  list_filter, date_hierarchy, search_fields, list_select_related,
                                                  list_per_page, list_max_show_all, list_editable, model_admin)
        self.title = _('Relatório de Lotes')

    def get_results(self, *args, **kwargs):
        super(LotReportChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(lot_cost_sum=Sum('lot_cost'))
        self.lot_cost_sum = q['lot_cost_sum']
        q = self.result_list.aggregate(voi_cost_sum=Sum('voi_cost'))
        self.voi_cost_sum = q['voi_cost_sum']
        q = self.result_list.aggregate(voi_profit_sum=Sum('voi_profit'))
        self.voi_profit_sum = q['voi_profit_sum']
        q = self.result_list.aggregate(voi_roi_sum=Sum('voi_roi'))
        self.voi_roi_sum = q['voi_roi_sum']
        q = self.result_list.aggregate(products_quantity_sum=Sum('products_quantity'))
        self.products_quantity_sum = q['products_quantity_sum']

    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse('admin:%s_%s_change' % (self.opts.app_label,
                                               'lot'),
                       args=(quote(pk),),
                       current_app=self.model_admin.admin_site.name)


class LotReportForm(forms.ModelForm):
    class Meta:
        model = LotReport
        exclude = []
        translation_from_date, translation_to_date = _('From date'), _('To date')


class LotReportAdmin(admin.ModelAdmin):
    form = LotReportForm

    list_display_links = ('id', 'name',)
    list_filter = [
        'collaborator',
        'status',
        ('create_date', DateRangeFilter),
        ('sell_date', DateRangeFilter),
        UserFilter,
        AsinFilter,
    ]

    search_fields = ('name', 'product__name',)
    list_display = ('id', 'name', 'collaborator', 'create_date', 'sell_date', 'status', 'lot_cost', 'voi_cost', 'voi_profit', 'voi_roi',
                    'products_quantity')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def get_changelist(self, request, **kwargs):
        return LotReportChangeList

    def get_queryset(self, request):
        qs = super(LotReportAdmin, self).get_queryset(request)
        qs = qs.filter(is_fake=False)
        return qs

admin_site.register(LotReport, LotReportAdmin)


class CollaboratorAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin_site.register(Collaborator, CollaboratorAdmin)


native_lookup_field = utils.lookup_field


def my_lookup_field(name, obj, model_admin=None):
    if name == 'action_checkbox' and ((str(model_admin) == 'store.LotAdmin' and obj.status == 2) or
                                      str(model_admin) == 'store.LotReportAdmin'):
        raise ObjectDoesNotExist
    return native_lookup_field(name, obj, model_admin=model_admin)

utils.lookup_field = my_lookup_field
