from django.contrib import admin
from utils.sites import admin_site
from stock.models import Product
from utils.models import Params
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from service.models import Service
from django.utils.translation import ugettext as _
import logging

logger = logging.getLogger('django')


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

    class Meta:
        model = Product
        fields = ('name', 'identifier', 'url', 'buy_price', 'sell_price', 'rank', 'quantity', 'fba_fee', 'amazon_fee',
                  'shipping_cost', 'redirect_services', 'condition', 'voi_value', 'notes')

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
        # self.fields['condition'].required = True

    def save(self, *args, **kwargs):
        instance = super(StockProductForm, self).save(commit=False)
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


class ProductAdmin(admin.ModelAdmin):
    form = StockProductForm
    search_fields = ('name', 'identifier',)
    list_display = ('identifier', 'name', 'quantity',)

admin_site.register(Product, ProductAdmin)
