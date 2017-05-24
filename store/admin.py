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
        label=_('Grupos')
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
        # Default save but no commit.
        instance = super(LotForm, self).save(commit=False)
        instance.groups = self.cleaned_data['groups']
        # Call save.
        instance.save()
        return instance


class LotProductInline(admin.StackedInline):
    model = Product
    formset = RequiredBaseInlineFormSet
    can_delete = True
    extra = 1
    verbose_name = _('Produto')
    verbose_name_plural = _('Produtos')


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
    list_display = ('id', 'name', 'status', 'create_date', 'sell_date', 'user')

admin.site.register(Lot, LotAdmin)
