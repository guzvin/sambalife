from django.contrib import admin
from utils.sites import admin_site
from stock.models import Product, Invoice
from utils.models import Params
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django import forms
from service.models import Service
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
from rangefilter.filter import DateRangeFilter

import logging

logger = logging.getLogger('django')


class RelatedAdminTextInputWidget(forms.TextInput):
    def __init__(self, attrs=None):
        self.attrs = {'class': 'vTextField'}
        self.choices = ()
        if attrs is not None:
            self.attrs.update(attrs)
        super(RelatedAdminTextInputWidget, self).__init__(attrs=self.attrs)


class ServiceModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name + ' - ' + str(obj.price)


class StockProductForm(forms.ModelForm):
    redirect_services = ServiceModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=True,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Serviços'), False),
        label=_('Serviços'),
        help_text=_('Serviços utilizados na preparação do envio.')
    )
    invoices = forms.ModelMultipleChoiceField(
        queryset=Invoice.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple('Invoices', False),
        label='Invoices',
        help_text=_('Invoices aos quais este produto pertence.')
    )

    class Meta:
        model = Product
        fields = ('name', 'identifier', 'url', 'buy_price', 'sell_price', 'rank', 'quantity', 'fba_fee', 'amazon_fee',
                  'shipping_cost', 'redirect_services', 'condition', 'voi_value', 'notes', 'invoices')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(StockProductForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            params = Params.objects.first()
            if params:
                self.fields['amazon_fee'].initial = params.amazon_fee
                self.fields['shipping_cost'].initial = params.shipping_cost
        else:

            # Populate the redirect_services field with the current Services.
            self.fields['redirect_services'].initial = self.instance.redirect_services.all()
            # self.fields['invoices'].queryset = Invoice.objects.filter(pk=self.instance.pk)
            self.fields['invoices'].initial = self.instance.invoices.all()
        # self.fields['condition'].required = True

    def save(self, *args, **kwargs):
        instance = super(StockProductForm, self).save(commit=False)
        try:
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
            instance.product_cost = instance.buy_price + instance.amazon_fee + instance.fba_fee + \
                instance.shipping_cost + redirect_cost
            instance.profit_per_unit = instance.sell_price - instance.product_cost
            instance.total_profit = instance.profit_per_unit * instance.quantity
            instance.roi = (instance.profit_per_unit / (instance.buy_price + redirect_cost)) * 100
            instance.save()
        except IntegrityError:
            pass  # o proprio django faz o tratamento da mensagem
        return instance


class MyRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):
    def render(self, name, value, *args, **kwargs):
        logger.debug('RRRRRRRRRRRRRRREEEEEEEEEEEEEEEEEEENNNNNNNNNNNNNNNNNNDDDDDDDDDDDDDDER')
        return ''

    def id_for_label(self, id_):
        logger.debug('WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW')
        return self.widget.id_for_label(id_)


class ProductAdmin(admin.ModelAdmin):
    form = StockProductForm
    search_fields = ('name', 'identifier',)
    list_display = ('identifier', 'name', 'quantity',)
    list_filter = [
        ('created_date', DateRangeFilter),
        ('changed_date', DateRangeFilter),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super(ProductAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)
        logger.debug('1@@@@@@@@@@@@@@@###############@@@@@@@@@@@@@@@@@################@@@@@@@@@@@@@@@@@')
        logger.debug(field)
        logger.debug(field.widget)
        if db_field.name == 'invoices':
            logger.debug('2@@@@@@@@@@@@@@@###############@@@@@@@@@@@@@@@@@################@@@@@@@@@@@@@@@@@')
            field.widget = MyRelatedFieldWidgetWrapper(
                field.widget.widget, db_field.remote_field, self.admin_site,
                can_add_related=True, can_change_related=True, can_delete_related=True
            )
            logger.debug(field)
            logger.debug(field.widget)
        return field

admin_site.register(Product, ProductAdmin)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = [
        'store',
        'origin',
    ]

admin_site.register(Invoice, InvoiceAdmin)
