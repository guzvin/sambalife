from django.db.models import Q
from utils.input_filter import InputFilter
from django.contrib.admin import SimpleListFilter
from store.models import Lot
from django.utils.translation import ugettext as _


class UserFilter(InputFilter):
    parameter_name = 'user'
    title = _('Usuário')

    def queryset(self, request, queryset):
        term = self.value()
        if term is None:
            return
        any_name = Q()
        for bit in term.split():
            any_name &= (
                Q(user__first_name__icontains=bit) |
                Q(user__last_name__icontains=bit) |
                Q(user__email__icontains=bit)
            )
        return queryset.filter(any_name)


class AsinFilter(InputFilter):
    parameter_name = 'asin'
    title = _('ASIN')

    def queryset(self, request, queryset):
        term = self.value()
        if term is None:
            return
        any_asin = Q()
        for bit in term.split():
            any_asin &= (
                Q(product__identifier__icontains=bit)
            )
        return queryset.filter(any_asin)


class LotStatusFilter(SimpleListFilter):
    parameter_name = 'lot_status'
    title = _('Status do lote')

    def lookups(self, request, model_admin):
        return [(choice[0], choice[1]) for choice in Lot.STATUS_CHOICES]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(lot__status=self.value())
