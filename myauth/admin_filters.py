from rangefilter.filter import DateRangeFilter
from django.utils.translation import ugettext as _
from django.contrib import admin
import datetime


class LotSellDateFilter(DateRangeFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(LotSellDateFilter, self).__init__(field, request, params, model, model_admin, field_path)
        self.title = _('Data de compra do lote')

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                return queryset.extra(
                    where=self._make_query_filter(request, validated_data)
                )
        return queryset

    def _make_query_filter(self, request, validated_data):
        query_params = []
        date_value_gte = validated_data.get(self.lookup_kwarg_gte, None)
        date_value_lte = validated_data.get(self.lookup_kwarg_lte, None)

        if date_value_gte:
            query_params.append('{} >= \'{}\''.format('store_lot.sell_date', str(self.make_dt_aware(
                datetime.datetime.combine(date_value_gte, datetime.time.min),
                self.get_timezone(request),
            ))))
        if date_value_lte:
            query_params.append('{} <= \'{}\''.format('store_lot.sell_date', str(self.make_dt_aware(
                datetime.datetime.combine(date_value_lte, datetime.time.max),
                self.get_timezone(request),
            ))))

        return query_params


class LotNoPurchaseFilter(admin.SimpleListFilter):
    title = _('Quem não comprou lote')
    parameter_name = 'lot_purchase'

    def lookups(self, request, model_admin):
        return [('1', _('Yes')), ('0', _('No'))]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.extra(
                        where=['store_lot.sell_date is null']
            )
        elif self.value() == '0':
            return queryset.extra(
                        where=['store_lot.sell_date is not null']
            )
        return queryset
