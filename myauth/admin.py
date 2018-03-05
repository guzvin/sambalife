from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.contrib.admin.utils import unquote
from django.contrib.admin import utils
from django.core.exceptions import ObjectDoesNotExist
from myauth.models import MyUser, UserAddress, UserLotReport
from django.db.models.fields import BLANK_CHOICE_DASH
from django.db.models import Q
from utils.sites import admin_site
from myauth.admin_filters import LotSellDateFilter, LotNoPurchaseFilter
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum

import logging

logger = logging.getLogger('django')


class GroupModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if obj.name == 'all_users':
            return str(_('Todos usuários'))
        if obj.name == 'admins':
            return str(_('Administradores do sistema'))
        return obj.name


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label=_('Senha'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirmação da senha'), widget=forms.PasswordInput)
    groups = GroupModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Grupos'), False),
        label=_('Grupos')
    )

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(UserCreationForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['email'].label = _('E-mail*')
        self.fields['first_name'].label = _('Nome*')
        self.fields['last_name'].label = _('Sobrenome*')
        self.fields['cell_phone'].label = _('Telefone 1*')
        self.fields['phone'].required = False

    class Meta:
        model = MyUser
        fields = ('email', 'first_name', 'last_name', 'cell_phone', 'phone', 'is_active', 'is_superuser')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Confirmação da senha inválida.'))
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.save()
        user.groups = self.cleaned_data['groups']
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()
    password1 = forms.CharField(label=_('Nova Senha'), widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label=_('Confirmação da senha'), widget=forms.PasswordInput, required=False)
    groups = GroupModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Grupos'), False),
        label=_('Grupos')
    )

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(UserChangeForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['email'].label = _('E-mail*')
        self.fields['password'].label = _('Senha*')
        # self.fields['first_name'].label = _('Nome*')
        self.fields['last_name'].label = _('Sobrenome*')
        self.fields['cell_phone'].label = _('Telefone 1*')
        self.fields['phone'].required = False
        # If it is an existing user (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['groups'].initial = self.instance.groups.all()

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'first_name', 'last_name', 'cell_phone', 'phone', 'is_active',
                  'is_superuser')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Confirmação da senha inválida.'))
        return password2

    def save(self, *args, **kwargs):
        # Default save but no commit.
        instance = super(UserChangeForm, self).save(commit=False)
        password = self.cleaned_data['password1']
        if password and password != '':
            instance.set_password(password)
        # Add the users to the Group.
        instance.groups = self.cleaned_data['groups']
        # Call save.
        instance.save()
        return instance


class UserAddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(UserAddressForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['country'].label = _('País*')
        self.fields['address_1'].label = _('Endereço*')
        self.fields['address_2'].required = False
        self.fields['zipcode'].label = _('CEP*')
        self.fields['state'].label = _('Estado*')
        self.fields['city'].label = _('Cidade*')
        self.fields['type'].label = _('Tipo*')

    class Meta:
        model = UserAddress
        fields = ('country', 'address_1', 'address_2', 'zipcode', 'state', 'city', 'type', 'default')


class AddressInline(admin.TabularInline):
    model = UserAddress
    form = UserAddressForm
    can_delete = True
    verbose_name = _('Endereço')
    verbose_name_plural = _('Endereços')


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    inlines = [
        AddressInline,
    ]

    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = _('1 usuário foi ativado.')
        else:
            message_bit = _('%s usuários foram ativados.') % rows_updated
        self.message_user(request, message_bit)
    make_active.short_description = _('Ativar Usuários selecionados')

    def make_inactive(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated == 1:
            message_bit = _('1 usuário foi desativado.')
        else:
            message_bit = _('%s usuários foram desativados.') % rows_updated
        self.message_user(request, message_bit)
    make_inactive.short_description = _('Desativar Usuários selecionados')

    def get_readonly_fields(self, request, obj=None):
        page_readonly_fields = self.readonly_fields
        if obj:
            if obj.first_name == 'Administrador':
                page_readonly_fields += ('first_name', 'is_superuser', 'is_active', 'is_verified',)
            if request.user.is_superuser is False and 'is_superuser' not in page_readonly_fields:
                page_readonly_fields += ('is_superuser',)
        return page_readonly_fields

    def get_action_choices(self, request, default_choices=BLANK_CHOICE_DASH):
        choices = super(UserAdmin, self).get_action_choices(request, default_choices)
        logger.debug('@@@@@@@@@@@@ USER ACTION CHOICES @@@@@@@@@@@@')
        logger.debug(choices)
        new_choices = []
        delete_action = None
        for a, b in choices:
            if a == 'delete_selected':
                delete_action = (a, b)
            else:
                new_choices.append((a, b))
        if delete_action:
            new_choices.append(('', '---------'))
            new_choices.append(delete_action)
        logger.debug(new_choices)
        return new_choices

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('id', 'email', 'date_joined', 'is_superuser', 'is_active', 'is_verified', 'partner')
    list_display_links = ('id', 'email',)
    list_filter = ('groups', 'is_superuser', 'is_active', 'is_verified', 'partner')
    readonly_fields = ('date_joined',)
    fieldsets = (
        (None, {'fields': ('date_joined', 'email', 'partner', 'password', 'is_verified', 'is_active',
                           'password1', 'password2')}),
        (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'cell_phone', 'phone',)}),
        (_('Permissões'), {'fields': ('is_superuser',)}),
        (_('Grupos'), {'fields': ('groups',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'partner', 'first_name', 'last_name', 'cell_phone', 'phone',
                       'is_verified', 'is_active', 'is_superuser', 'password1', 'password2', 'groups')}
         ),
    )

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj is None:
            if request.user.is_superuser is False:
                self.add_fieldsets = (
                    (None, {
                        'classes': ('wide',),
                        'fields': ('email', 'partner', 'first_name', 'last_name', 'cell_phone', 'phone',
                                   'is_verified', 'is_active', 'password1', 'password2', 'groups')}
                     ),
                )
                kwargs['fields'] = ('email', 'partner', 'first_name', 'last_name', 'cell_phone', 'phone',
                                    'is_verified', 'is_active', 'password1', 'password2', 'groups')
        return super(UserAdmin, self).get_form(request, obj, **kwargs)

    search_fields = ('id', 'email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        this_extra_context = extra_context
        check_system_user = self.model.objects.get(pk=unquote(object_id))
        if check_system_user.first_name == 'Administrador':
            check_system_user.first_name = str(_('Administrador'))
            system_user_extra_context = dict(
                original=check_system_user,
                show_delete=False,
            )
            if this_extra_context is None:
                this_extra_context = {}
            this_extra_context.update(system_user_extra_context)
        if not request.user.is_superuser:
            self.list_display = ('id', 'email', 'date_joined', 'is_active', 'is_verified', 'partner')
            self.list_filter = ('groups', 'is_active', 'is_verified', 'partner')
            self.fieldsets = (
                (None, {'fields': ('date_joined', 'email', 'partner', 'password', 'is_verified', 'is_active',
                                   'password1', 'password2')}),
                (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'cell_phone', 'phone',)}),
                (_('Grupos'), {'fields': ('groups',)}),
            )
        return super(UserAdmin, self).change_view(request, object_id, form_url=form_url,
                                                  extra_context=this_extra_context)

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            self.list_display = ('id', 'email', 'date_joined', 'is_active', 'is_verified', 'partner')
            self.list_filter = ('groups', 'is_active', 'is_verified', 'partner')
            self.fieldsets = (
                (None, {'fields': ('date_joined', 'email', 'partner', 'password', 'is_verified', 'is_active',
                                   'password1', 'password2')}),
                (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'cell_phone', 'phone',)}),
                (_('Grupos'), {'fields': ('groups',)}),
            )
        return super(UserAdmin, self).changelist_view(request, extra_context)

# admin.site.unregister(MyUser)
# Now register the new UserAdmin...
admin_site.register(MyUser, UserAdmin)


User = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.id, obj.email)


class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = UserModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple(_('Usuários'), False),
        label=_('Usuários')
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    def save(self, *args, **kwargs):
        # Default save but no commit.
        instance = super(GroupAdminForm, self).save(commit=False)
        if instance.pk is None:
            instance.save()
        # Add the users to the Group.
        instance.user_set = self.cleaned_data['users']
        # Call save.
        instance.save()
        return instance


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']

    list_display = ('translated_name',)

    def translated_name(self, obj):
        if obj.name == 'all_users':
            return _('Todos usuários')
        if obj.name == 'admins':
            return _('Administradores do sistema')
        return obj.name

    translated_name.short_description = _('Nome')

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.name == 'all_users' or obj.name == 'admins'):
            return self.readonly_fields + ('translated_name',)
        return self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj and obj.name == 'admins':  # obj is not None, so this is a change page
            if not request.user.is_superuser:
                self.fieldsets = (
                    (None, {'fields': ('translated_name', 'users')}),
                )
                kwargs['fields'] = ('translated_name', 'users')
            else:  # obj is None, so this is an add page
                self.fieldsets = (
                    (None, {'fields': ('name', 'permissions', 'users')}),
                )
                kwargs['fields'] = ('name', 'permissions', 'users')
        elif obj and obj.name == 'all_users':  # obj is not None, so this is a change page
            self.fieldsets = (
                (None, {'fields': ('translated_name', 'permissions', 'users')}),
            )
            kwargs['fields'] = ('translated_name', 'permissions', 'users')
        else:  # obj is None, so this is an add page
            self.fieldsets = (
                (None, {'fields': ('name', 'permissions', 'users')}),
            )
            kwargs['fields'] = ('name', 'permissions', 'users')
        return super(GroupAdmin, self).get_form(request, obj, **kwargs)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        this_extra_context = extra_context
        check_system_group = self.model.objects.get(pk=unquote(object_id))
        if check_system_group.name == 'all_users' or check_system_group.name == 'admins':
            check_system_group.name = str(_('Todos usuários')) if check_system_group.name == 'all_users' \
                else str(_('Administradores do sistema'))
            system_group_extra_context = dict(
                original=check_system_group,
                show_delete=False,
            )
            if this_extra_context is None:
                this_extra_context = {}
            this_extra_context.update(system_group_extra_context)
        return super(GroupAdmin, self).change_view(request, object_id, form_url=form_url,
                                                   extra_context=this_extra_context)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super(GroupAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'permissions' and request.user.is_superuser is False:
            field.queryset = field.queryset.filter(Q(content_type__app_label__in=[
                'admin', 'auth', 'myauth', 'product', 'shipment', 'payment', 'store']) & ~Q(content_type__model__in=[
                    'estimates', 'permission', 'costformula']))
        return field

# Register the new Group ModelAdmin.
admin_site.register(Group, GroupAdmin)


class UserLotReportChangeList(ChangeList):
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable, model_admin):
        self.lot_cost_sum = None
        super(UserLotReportChangeList, self).__init__(request, model, list_display, list_display_links,
                                                      list_filter, date_hierarchy, search_fields, list_select_related,
                                                      list_per_page, list_max_show_all, list_editable, model_admin)
        self.title = _('Relatório Usuário x Lote')

    def get_results(self, *args, **kwargs):
        super(UserLotReportChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(lot_cost_sum=Sum('lot__lot_cost'))
        self.lot_cost_sum = q['lot_cost_sum']


class UserLotReportForm(forms.ModelForm):
    class Meta:
        model = UserLotReport
        exclude = []


class UserLotReportAdmin(admin.ModelAdmin):
    form = UserLotReportForm

    # list_display_links = ('id', 'name',)
    list_filter = [
        'groups',
        ('lot__sell_date', LotSellDateFilter),
        LotNoPurchaseFilter,
    ]

    #  DO NOTHING CHECK get_search_results FOR SEARCH FIELDS
    search_fields = ('first_name', 'last_name', 'email', 'lot__name')
    list_display = ('id', 'user_name', 'email', 'user_date_joined', 'lot_name', 'lot_sell_date', 'lot_cost',)

    def user_name(self, obj):
        return ' '.join([obj.first_name, obj.last_name])

    user_name.short_description = _('Nome usuário')

    def user_date_joined(self, obj):
        return obj.date_joined

    user_date_joined.short_description = _('Data de cadastro do usuário')

    def lot_name(self, obj):
        return obj.lot_name

    lot_name.short_description = _('Lote')

    def lot_sell_date(self, obj):
        return obj.lot_sell_date

    lot_sell_date.short_description = _('Data de compra do lote')

    def lot_cost(self, obj):
        return obj.lot_cost

    lot_cost.short_description = _('Valor de compra do lote')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def get_changelist(self, request, **kwargs):
        return UserLotReportChangeList

    def get_queryset(self, request):
        qs = super(UserLotReportAdmin, self).get_queryset(request)
        qs = qs.filter(Q(lot__name__isnull=True) | Q(lot__is_fake=False)).extra(
            select={'lot_name': 'store_lot.name', 'lot_sell_date': 'store_lot.sell_date',
                    'lot_cost': 'store_lot.lot_cost'}
        ).order_by('first_name', 'last_name', '-lot__sell_date')
        return qs

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            for bit in search_term.split():
                queryset = queryset.extra(where=['UPPER(myauth_myuser.first_name::text) LIKE UPPER(%s) OR '
                                                 'UPPER(myauth_myuser.last_name::text) LIKE UPPER(%s) OR '
                                                 'UPPER(myauth_myuser.email::text) LIKE UPPER(%s) OR '
                                                 'UPPER(store_lot.name::text) LIKE UPPER(%s)'],
                                          params=['%{}%'.format(bit),
                                                  '%{}%'.format(bit),
                                                  '%{}%'.format(bit),
                                                  '%{}%'.format(bit)])
            # for bit in search_term.split():
            #     if where_clauses:
            #         where_clauses.append('OR')
            #     where_clauses.append('UPPER(myauth_myuser.first_name::text) LIKE UPPER(%s) OR '
            #                          'UPPER(myauth_myuser.last_name::text) LIKE UPPER(%s) OR '
            #                          'UPPER(myauth_myuser.email::text) LIKE UPPER(%s) OR '
            #                          'UPPER(store_lot.name::text) LIKE UPPER(%s)')
            #     where_params.append('%{}%'.format(bit))
            #     where_params.append('%{}%'.format(bit))
            #     where_params.append('%{}%'.format(bit))
            #     where_params.append('%{}%'.format(bit))
            # queryset = queryset.extra(where=[' '.join(where_clauses)], params=where_params)
        return queryset, True

admin_site.register(UserLotReport, UserLotReportAdmin)


native_lookup_field = utils.lookup_field


def my_lookup_field(name, obj, model_admin=None):
    logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    logger.debug(str(obj))
    logger.debug(str(model_admin))
    logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    if name == 'action_checkbox' \
            and (str(model_admin) == 'auth.GroupAdmin' or str(model_admin) == 'myauth.UserAdmin') \
            and (str(obj) == 'all_users' or str(obj) == 'admins' or
                    (str(model_admin) == 'myauth.UserAdmin' and str(obj.first_name) == 'Administrador')):
        raise ObjectDoesNotExist
    return native_lookup_field(name, obj, model_admin=model_admin)

utils.lookup_field = my_lookup_field
