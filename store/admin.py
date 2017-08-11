from django import forms
from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.contrib.admin.utils import unquote
from django.contrib.admin import utils
from django.core.exceptions import ObjectDoesNotExist
from store.models import Lot, Product
from django.db.models.fields import BLANK_CHOICE_DASH
from utils.helper import RequiredBaseInlineFormSet
from utils.models import Params
from utils.sites import admin_site
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
            # Populate the users field with the current Group users.
            self.fields['groups'].initial = self.instance.groups.all()

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
    formset = RequiredBaseInlineFormSet
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
        'payment_complete',
    ]

    search_fields = ('name', 'product__name',)
    list_display_links = ('id', 'name',)
    list_display = ('id', 'name', 'payment_complete', 'status', 'create_date', 'sell_date', 'user')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'groups')}),
    )

    def save_related(self, request, form, formsets, change):
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
                products_cost += product.product_cost * product.quantity
                profit += product.total_profit
                average_roi += (product.roi / 100)
                lot_cost += (product.buy_price * product.quantity)
                redirect_cost += (product.redirect_factor * product.quantity)
            lot.products_cost = products_cost
            lot.profit = profit
            lot.average_roi = (average_roi / len(products)) * 100
            lot.lot_cost = lot_cost
            lot.redirect_cost = redirect_cost
            lot.save()

admin_site.register(Lot, LotAdmin)
