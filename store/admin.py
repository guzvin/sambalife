from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms.widgets import HiddenInput
from django.contrib.admin.options import TO_FIELD_VAR
from django.contrib.auth.models import Group
from django.db.models import Sum, F
from django.db.models.fields import FloatField
from store.models import Lot, Product, Config, LotReport, lot_directory_path, Collaborator
from store.admin_filters import UserFilter, AsinFilter
from stock.models import Product as ProductStock
from product.models import Product as ProductProduct
from store.widgets import NameTextInput, IdentifierTextInput, UpcTextInput
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
from django.core.validators import ValidationError
from store.send_email import email_new_lot, email_new_lot_lifecycle
import datetime
import pytz
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
            if 'groups' in self.fields:
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

    def is_valid(self):
        request = get_current_request()
        if request.method == 'POST':
            request.POST = request.POST.copy()
            # situacoes: (1)nao era fake nem arquivado e passou a ser ;; (2)era fake e/ou arquivado e deixou de ser
            # (0)se fake e/ou arquivado se mantem nao mexe no estoque _ignore_stock
            # (1)tem produtos do estoque que precisam ser devolvidos ao estoque _return_to_stock
            # (2)precisa fazer a verificacao/retirada dos produtos do estoque _get_from_stock
            initial_fake = self.inline_initial_data('is_fake')
            initial_archived = self.inline_initial_data('is_archived')
            logger.debug(self.instance.pk)
            logger.debug(initial_fake[0] is True)
            logger.debug(initial_fake[1] is True)
            logger.debug(initial_archived[0] is True)
            logger.debug(initial_archived[1] is True)
            if self.instance.pk is None:
                request.POST['_ignore_stock'] = initial_fake[1] or initial_archived[1]
            else:
                if initial_fake[0] is False and initial_archived[0] is False and (initial_fake[1]
                                                                                  or initial_archived[1]):
                    request.POST['_return_to_stock'] = True
                elif initial_fake[1] is False and initial_archived[1] is False and (initial_fake[0]
                                                                                    or initial_archived[0]):
                    request.POST['_get_from_stock'] = True
                elif (initial_fake[0] or initial_archived[0]) and (initial_fake[1] or initial_archived[1]):
                    request.POST['_ignore_stock'] = True
        return super(LotForm, self).is_valid()

    def inline_initial_data(self, field_name):
        if field_name not in self.fields:
            return None, None
        name, field = field_name, self.fields[field_name]
        prefixed_name = self.add_prefix(name)
        data_value = field.widget.value_from_datadict(self.data, self.files, prefixed_name)
        if not field.show_hidden_initial:
            initial_value = self.initial.get(name, field.initial)
            if callable(initial_value):
                initial_value = initial_value()
        else:
            initial_prefixed_name = self.add_initial_prefix(name)
            hidden_widget = field.hidden_widget()
            try:
                initial_value = field.to_python(hidden_widget.value_from_datadict(
                    self.data, self.files, initial_prefixed_name))
            except ValidationError:
                # Always assume data has changed if validation fails.
                return None
        return initial_value, data_value


class LotProductFormSet(helper.RequiredBaseInlineFormSet):
    def clean(self):
        logger.debug('@!@!@!@!#@#@#@#@#@#!@#!@#!@#!@#!@#!@#!@#!@#@!#!@#!@#!@#@!#')
        super(LotProductFormSet, self).clean()
        stock_product_quantity_dict = {}
        new_product_quantity_dict = {}
        errors_dict = {}
        forms_dict = {}
        forms_valid = True
        for form in self.forms:
            logger.debug(form.data.get('_ignore_stock', False))
            logger.debug(form.data.get('_return_to_stock', False))
            logger.debug(form.data.get('_get_from_stock', False))
            if form.data.get('_ignore_stock', False) or not form.cleaned_data:
                continue
            if forms_valid and (form.is_valid() is False or form.data.get('_lot_obj', None) is None):
                forms_valid = False
            old_stock_product_id = None
            stock_product = None
            stock_product_id = form['product_stock'].value() if 'product_stock' in form else []
            if len(stock_product_id) == 0:
                identifier = form.cleaned_data.get('identifier')
                if identifier is None:
                    continue
                stock_product = ProductStock.objects.filter(identifier=identifier)
                if stock_product:
                    stock_product_id = stock_product[0].id
                    form.instance.product_stock = stock_product[0]
                elif form.data.get('_return_to_stock', False) is False:
                    error_key = ''.join(['asin', identifier])
                    if error_key not in errors_dict:
                        errors_dict[error_key] = [_('Produto, ASIN: %(asin)s, não existe no estoque. Primeiro faça o '
                                                    'cadastro dele lá para depois adicioná-lo a algum lote.') % {
                            'asin': identifier
                        }]
                    continue
            product_qty = form.inline_initial_data('quantity')
            logger.debug(product_qty)
            if product_qty is None or len(product_qty[1]) == 0:
                stock_product_quantity_dict = {}
                new_product_quantity_dict = {}
                errors_dict = {}
                forms_dict = {}
                break
            product_qty = product_qty[0], int(product_qty[1])
            logger.debug(product_qty[0])
            logger.debug(product_qty[1])
            if product_qty[1] == 0:
                form.add_error('quantity', _('This field is required.'))
            if str(stock_product_id) not in stock_product_quantity_dict:
                if stock_product is None:
                    stock_product = ProductStock.objects.filter(pk=stock_product_id)
                if stock_product:
                    stock_product_quantity_dict[str(stock_product_id)] = stock_product[0].quantity
                elif form.data.get('_return_to_stock', False) is False:
                    raise ValidationError([_('Ocorreu um erro de inconsistência! Saia e entre desta operação para '
                                             'tentar novamente e, caso o problema persista, entre em contato com '
                                             'os responsáveis pelo sistema.')])
            old_stock_product_id = LotProductFormSet.switch_products(form, new_product_quantity_dict,
                                                                     old_stock_product_id, product_qty,
                                                                     stock_product_quantity_dict)
            if form.cleaned_data.get('DELETE'):
                form.instance.custom = 'IGNORE ON DELETE SIGNAL'
                if old_stock_product_id is None and form.data.get('_get_from_stock', False) is False and product_qty[0]:
                    stock_product_quantity_dict[str(stock_product_id)] = \
                        stock_product_quantity_dict[str(stock_product_id)] + product_qty[0]
                continue
            if str(stock_product_id) not in forms_dict:
                forms_dict[str(stock_product_id)] = [form]
            else:
                forms_dict[str(stock_product_id)].append(form)
            if old_stock_product_id is None and form.data.get('_get_from_stock', False) is False and product_qty[0]:
                stock_product_quantity_dict[str(stock_product_id)] = \
                    stock_product_quantity_dict[str(stock_product_id)] + product_qty[0]
            if str(stock_product_id) in new_product_quantity_dict:
                new_product_quantity_dict[str(stock_product_id)] = \
                    new_product_quantity_dict[str(stock_product_id)] + product_qty[1]
            else:
                new_product_quantity_dict[str(stock_product_id)] = product_qty[1]
        for key, form in forms_dict.items():
            stock_quantity = stock_product_quantity_dict[key]
            if form[0].data.get('_return_to_stock', False):
                if forms_valid:
                    ProductStock.objects.filter(pk=key).update(quantity=stock_quantity)
                continue
            products_quantity = new_product_quantity_dict[key]
            if stock_quantity < products_quantity:
                if key not in errors_dict:
                    errors_dict[key] = [_('Quantidade em estoque (%(qty)s) menor que a informada (%(qty2)s) para o '
                                          'produto de ASIN: %(asin)s.') % {
                        'qty': stock_quantity,
                        'qty2': products_quantity,
                        'asin': form[0].cleaned_data.get('identifier')
                    }]
                for f in form:
                    f.add_error('quantity', _('Verifique esta quantidade!'))
            stock_product_quantity_dict[key] = stock_quantity - products_quantity
        if errors_dict:
            raise ValidationError([m for k, m in errors_dict.items()])
        if forms_valid:
            for key, qty in stock_product_quantity_dict.items():
                ProductStock.objects.filter(pk=key).update(quantity=qty)

    @staticmethod
    def switch_products(form, new_product_quantity_dict, old_stock_product_id, product_qty,
                        stock_product_quantity_dict):
        product_identifier = form.inline_initial_data('identifier')
        logger.debug(product_identifier)
        if product_identifier[0] and product_identifier[0] != product_identifier[1]:
            old_stock_product = ProductStock.objects.filter(identifier=product_identifier[0])
            if old_stock_product:
                old_stock_product_id = old_stock_product[0].id
                if str(old_stock_product_id) not in stock_product_quantity_dict:
                    stock_product_quantity_dict[str(old_stock_product_id)] = old_stock_product[0].quantity
                if form.data.get('_get_from_stock', False) is False and product_qty[0]:
                    stock_product_quantity_dict[str(old_stock_product_id)] = \
                        stock_product_quantity_dict[str(old_stock_product_id)] + product_qty[0]
                if str(old_stock_product_id) not in new_product_quantity_dict:
                    new_product_quantity_dict[str(old_stock_product_id)] = 0
        return old_stock_product_id


class LotProductForm(forms.ModelForm):
    is_duplicating = False
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
        widgets = {
            'product_stock': HiddenInput(),
            'name': NameTextInput(),
            'identifier': IdentifierTextInput(),
            'upc': UpcTextInput()
        }
        fields = ('name', 'identifier', 'upc', 'pick_ticket', 'url', 'buy_price', 'sell_price', 'rank',
                  'quantity', 'fba_fee', 'amazon_fee', 'shipping_cost', 'redirect_services', 'condition', 'voi_value',
                  'notes', 'product_stock')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(LotProductForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            params = Params.objects.first()
            if params:
                if 'amazon_fee' in self.fields:
                    self.fields['amazon_fee'].initial = params.amazon_fee
                if 'shipping_cost' in self.fields:
                    self.fields['shipping_cost'].initial = params.shipping_cost
        else:
            if self.is_duplicating is False and self.instance.lot.status == 2 and self.instance.lot.payment_complete:
                del self.fields['redirect_services']
            # Populate the redirect_services field with the current Services.
            if 'redirect_services' in self.fields:
                self.fields['redirect_services'].initial = self.instance.redirect_services.all()
        # self.fields['condition'].required = True

    def save(self, *args, **kwargs):
        instance = super(LotProductForm, self).save(commit=False)
        if instance.pk is None:
            instance.save()
        else:
            ProductProduct.objects.filter(lot_product=instance).update(pick_ticket=self.cleaned_data['pick_ticket'])
        if 'redirect_services' in self.fields:
            redirect_cost = 0
            logger.debug(self.fields)
            instance.redirect_services = self.cleaned_data['redirect_services']
            logger.debug('@@@@@@@@@@@@@ REDIRECT COST @@@@@@@@@@@@@@@@')
            logger.debug(instance.redirect_services)
            for redirect_service in instance.redirect_services.all():
                logger.debug(redirect_service.price)
                redirect_cost += redirect_service.price
            logger.debug(redirect_cost)
            instance.product_cost = instance.buy_price + instance.amazon_fee + instance.fba_fee + \
                instance.shipping_cost + redirect_cost
            instance.profit_per_unit = instance.sell_price - instance.product_cost
            instance.total_profit = instance.profit_per_unit * instance.quantity
            instance.roi = (instance.profit_per_unit / (instance.buy_price + redirect_cost)) * 100
        instance.save()
        return instance

    def inline_initial_data(self, field_name):
        name, field = field_name, self.fields[field_name]
        prefixed_name = self.add_prefix(name)
        data_value = field.widget.value_from_datadict(self.data, self.files, prefixed_name)
        if not field.show_hidden_initial:
            initial_value = self.initial.get(name, field.initial)
            if callable(initial_value):
                initial_value = initial_value()
        else:
            initial_prefixed_name = self.add_initial_prefix(name)
            hidden_widget = field.hidden_widget()
            try:
                initial_value = field.to_python(hidden_widget.value_from_datadict(
                    self.data, self.files, initial_prefixed_name))
            except ValidationError:
                # Always assume data has changed if validation fails.
                return None
        return initial_value, data_value


class LotProductInline(admin.StackedInline):
    template = 'admin/edit_inline/store/lot/stacked.html'
    model = Product
    formset = LotProductFormSet
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

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(LotProductInline, self).get_formset(request, obj, **kwargs)
        formset.form.is_duplicating = request.GET.get('duplicate_lot', False)
        return formset

    def get_fields(self, request, obj=None):
        if self.fields:
            return self.fields
        form = self.get_formset(request, obj, fields=None).form
        if obj and obj.status == 2 and obj.payment_complete:
            del form.base_fields['redirect_services']
        return list(form.base_fields) + list(self.get_readonly_fields(request, obj))

    def get_readonly_fields(self, request, obj=None):
        page_readonly_fields = self.readonly_fields
        if obj and obj.status == 2 and obj.payment_complete:
            page_readonly_fields += ('name', 'identifier', 'upc', 'url', 'buy_price', 'sell_price', 'rank', 'quantity',
                                     'fba_fee', 'amazon_fee', 'shipping_cost', 'redirect_services', 'condition',
                                     'notes', 'product_stock')
        page_readonly_fields += ('roi',)
        return page_readonly_fields

    def get_queryset(self, request):
        qs = super(LotProductInline, self).get_queryset(request)
        # for p in qs:
        #     redirect_cost = 0
        #     for redirect_service in p.redirect_services.all():
        #         redirect_cost += redirect_service.price
        #     logger.info('profit_per_unit ==> %s' % str(p.profit_per_unit))
        #     logger.info('buy_price ==> %s' % str(p.buy_price))
        #     logger.info('redirect_cost ==> %s' % str(redirect_cost))
        #     p.roi = (p.profit_per_unit / (p.buy_price + redirect_cost)) * 100
        #     logger.info('roi ==> %s' % str(p.roi))
        #     p.save()
        return qs


class ExampleChangeList(ChangeList):
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable, model_admin):
        super(ExampleChangeList, self).__init__(request, model, list_display, list_display_links,
                                                list_filter, date_hierarchy, search_fields, list_select_related,
                                                list_per_page, list_max_show_all, list_editable, model_admin)
        # self.show_all = True

    def get_results(self, *args, **kwargs):
        super(ExampleChangeList, self).get_results(*args, **kwargs)
        # for lot in self.result_list:
        #     lot.average_roi = (lot.profit / lot.lot_cost) * 100
        #     lot.save()


class LotAdmin(admin.ModelAdmin):
    form = LotForm

    inlines = [
        LotProductInline,
    ]

    list_filter = [
        'destination',
        'is_archived',
        'status',
        'is_fake',
        'lifecycle',
        ('create_date', DateRangeFilter),
        ('sell_date', DateRangeFilter),
    ]

    search_fields = ('name', 'product__name', 'product__identifier', 'product__upc',)
    list_display_links = ('id', 'name',)
    list_display = ('id', 'destination', 'name', 'create_date', 'average_roi', 'products_quantity', 'status',
                    'lot_cost', 'sell_date', 'schedule_date', 'is_archived', 'is_fake', 'duplicate_lot_action')

    def duplicate_lot_action(self, obj):
        return format_html('<a class="button" href="{}">{}</a>', reverse('admin:duplicate_lot',
                                                                         args=[obj.pk]), _('Duplicar lote'))
    duplicate_lot_action.short_description = _('Duplicar')
    duplicate_lot_action.allow_tags = True

    fieldsets = (
        (_('Status'), {
            'fields': (
                'is_fake', 'is_archived', 'lifecycle',
            )
        }),
        (_('Situação'), {
            'fields': (
                'status', 'sell_date',
            )
        }),
        (_('Agendamento'), {
            'description': _('Os lotes agendados somente ficam disponíveis na lista na data agendada.'),
            'fields': (
                'schedule_date',
            )
        }),
        (_('Informações'), {
            'fields': (
                'destination', 'name', 'order_weight', 'description', 'collaborator', 'thumbnail', 'groups',
            )
        }),
    )

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            self.list_display = ('id', 'email', 'from_key', 'date_joined', 'is_active', 'is_verified', 'partner')
            self.list_filter = ('groups', 'is_active', 'is_verified', 'partner')
            self.fieldsets = (
                (None, {'fields': ('date_joined', 'email', 'partner', 'password', 'is_verified', 'is_active',
                                   'password1', 'password2')}),
                (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'amz_store_name', 'cell_phone',
                                                      'phone',)}),
                (_('Permissões'), {'fields': ('collaborator',)}),
                (_('Grupos'), {'fields': ('groups',)}),
            )
        return super(LotAdmin, self).changelist_view(request, extra_context)

    def save_form(self, request, form, change):
        lot_obj = super(LotAdmin, self).save_form(request, form, change)
        logger.debug('@@@@@@@@@@!!!!!!!!!!SAVE FORM!!!!!!!!@@@@@@@@@@@@@@@')
        if request.method == 'POST':
            if lot_obj.payment_complete is False:
                is_fake = form.inline_initial_data('is_fake')
                is_archived = form.inline_initial_data('is_archived')
                status = form.inline_initial_data('status')
                status = status[0], int(status[1]),
                schedule_date = form.inline_initial_data('schedule_date')
                schedule_date = schedule_date[0], form.cleaned_data.get('schedule_date'),
                if status[1] == 2:
                    lot_obj.payment_complete = True
                    sell_date = form.cleaned_data.get('sell_date')
                    if sell_date is None:
                        lot_obj.sell_date = pytz.utc.localize(datetime.datetime.today())
                else:
                    lot_obj.payment_complete = False
                    lot_obj.sell_date = None
                if schedule_date[1] and schedule_date[1] <= datetime.datetime.now(datetime.timezone.utc):
                    lot_obj.schedule_date = None
                if lot_obj.schedule_date is None and lot_obj.payment_complete is False and is_fake[1] is False \
                        and is_archived[1] is False:
                    initial_lifecycle = form.inline_initial_data('lifecycle')
                    initial_lifecycle = initial_lifecycle[0], int(initial_lifecycle[1]),
                    if not change or initial_lifecycle[0] != initial_lifecycle[1] or schedule_date[0] != schedule_date[1] \
                            or status[0] != status[1] or is_fake[0] != is_fake[1] or is_archived[0] != is_archived[1]:
                        if initial_lifecycle[1] == 2 or initial_lifecycle[1] == 4:
                            lot_obj.lifecycle_date = pytz.utc.localize(datetime.datetime.today())
                            if initial_lifecycle[1] == 4:
                                form.cleaned_data['groups'] = form.cleaned_data.get('groups') | \
                                    Group.objects.filter(name='all_users')
                                lot_obj.lifecycle_open = True
                            else:
                                lot_obj.lifecycle_open = False
                        else:
                            lot_obj.lifecycle_date = None
                            lot_obj.lifecycle_open = False
                else:
                    lot_obj.lifecycle_date = None
                    lot_obj.lifecycle_open = False
            request.POST = request.POST.copy()
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
        if lot.is_fake is False and lot.is_archived is False and lot.status == 1 and lot.payment_complete is False \
                and (lot.schedule_date is None or lot.schedule_date <= datetime.datetime.now(datetime.timezone.utc)):
            if change is False or change and is_archived_changed:
                if lot.lifecycle == 2 or lot.lifecycle == 4:
                    email_new_lot_lifecycle(lot)
                else:
                    email_new_lot(lot)

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

    def get_changelist(self, request, **kwargs):
        return ExampleChangeList

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

    def get_readonly_fields(self, request, obj=None):
        page_readonly_fields = self.readonly_fields
        if obj and obj.status == 2 and obj.payment_complete:
            page_readonly_fields += ('is_fake', 'status', 'lifecycle', 'sell_date', 'payment_complete', 'schedule_date',
                                     'destination', 'name', 'order_weight', 'description', 'collaborator', 'thumbnail',
                                     'groups')
        return page_readonly_fields

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
        self.products_quantity_sum = None
        self.paypal_value_sum = None
        self.transfer_value_sum = None
        self.net_value_sum = None
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
        q = self.result_list.aggregate(products_quantity_sum=Sum('products_quantity'))
        self.products_quantity_sum = q['products_quantity_sum']
        params = Params.objects.first()
        if params:
            q = self.result_list.aggregate(paypal_value_sum=Sum((F('lot_cost') * params.paypal_fee) / 100,
                                           output_field=FloatField()))
            self.paypal_value_sum = q['paypal_value_sum']
            q = self.result_list.aggregate(transfer_value_sum=Sum(F('products_quantity') * params.fgr_cost,
                                           output_field=FloatField()))
            self.transfer_value_sum = q['transfer_value_sum']
            q = self.result_list.aggregate(net_value_sum=Sum(F('lot_cost') -
                                                             ((F('lot_cost') * params.paypal_fee) / 100) -
                                                             (F('products_quantity') * params.fgr_cost),
                                                             output_field=FloatField()))
            self.net_value_sum = q['net_value_sum']

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

    search_fields = ('name', 'product__name', 'product__identifier', 'product__upc',
                     'product__product_stock__invoices__name')
    list_display = ('id', 'destination', 'name', 'collaborator', 'create_date', 'sell_date', 'status', 'lot_cost',
                    'voi_cost', 'voi_profit', 'voi_roi', 'products_quantity', 'paypal_value', 'transfer_value',
                    'net_value')

    def paypal_value(self, obj):
        params = Params.objects.first()
        if params:
            return round((obj.lot_cost * params.paypal_fee) / 100, 2)
        return _('É preciso cadastrar os parâmetros da aplicação.')
    paypal_value.short_description = _('Desconto PayPal')

    def transfer_value(self, obj):
        params = Params.objects.first()
        if params:
            return obj.products_quantity * params.fgr_cost
        return _('É preciso cadastrar os parâmetros da aplicação.')
    transfer_value.short_description = _('Valor de Repasse')

    def net_value(self, obj):
        paypal_value = self.paypal_value(obj)
        transfer_value = self.transfer_value(obj)
        if paypal_value == _('É preciso cadastrar os parâmetros da aplicação.') or \
                transfer_value == _('É preciso cadastrar os parâmetros da aplicação.'):
            return _('É preciso cadastrar os parâmetros da aplicação.')
        return obj.lot_cost - paypal_value - transfer_value
    net_value.short_description = _('Valor Real')

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
