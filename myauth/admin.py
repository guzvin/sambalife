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
from myauth.models import MyUser, UserAddress
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
        self.fields['doc_number'].label = _('CPF*')
        self.fields['cell_phone'].label = _('Celular*')
        self.fields['phone'].required = False

    class Meta:
        model = MyUser
        fields = ('email', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone', 'is_active', 'is_superuser')

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
        user.set_password(self.cleaned_data["password1"])
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
        self.fields['doc_number'].label = _('CPF*')
        self.fields['cell_phone'].label = _('Celular*')
        self.fields['phone'].required = False
        # If it is an existing user (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['groups'].initial = self.instance.groups.all()

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone', 'is_active',
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
        password = self.cleaned_data["password1"]
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
        self.fields['address_1'].label = _('Endereço*')
        self.fields['address_2'].required = False
        self.fields['neighborhood'].label = _('Bairro*')
        self.fields['zipcode'].label = _('CEP*')
        self.fields['state'].label = _('Estado*')
        self.fields['city'].label = _('Cidade*')
        self.fields['type'].label = _('Tipo*')

    class Meta:
        model = UserAddress
        fields = ('address_1', 'address_2', 'neighborhood', 'zipcode', 'state', 'city', 'type', 'default')


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

    def get_readonly_fields(self, request, obj=None):
        page_readonly_fields = self.readonly_fields
        if obj:
            if obj.first_name == 'Administrador':
                page_readonly_fields += ('first_name', 'is_superuser', 'is_active', 'is_verified',)
            if request.user.is_superuser is False and 'is_superuser' not in page_readonly_fields:
                page_readonly_fields += ('is_superuser',)
        return page_readonly_fields

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('id', 'email', 'is_superuser', 'is_active', 'is_verified')
    list_display_links = ('id', 'email',)
    list_filter = ('is_superuser', 'is_active', 'is_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_verified', 'password1', 'password2')}),
        (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'doc_number', 'phone', 'cell_phone',
                                              'is_active',)}),
        (_('Permissões'), {'fields': ('is_superuser',)}),
        (_('Grupos'), {'fields': ('groups',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone', 'is_verified',
                       'is_active', 'is_superuser', 'password1', 'password2', 'groups')}
         ),
    )

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj is None:
            if request.user.is_superuser is False:
                self.add_fieldsets = (
                    (None, {
                        'classes': ('wide',),
                        'fields': ('email', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone',
                                   'is_verified', 'is_active', 'password1', 'password2', 'groups')}
                     ),
                )
                kwargs['fields'] = ('email', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone',
                                    'is_verified', 'is_active', 'password1', 'password2', 'groups')
        return super(UserAdmin, self).get_form(request, obj, **kwargs)

    search_fields = ('id', 'email',)
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
        return super(UserAdmin, self).change_view(request, object_id, form_url=form_url,
                                                  extra_context=this_extra_context)

# admin.site.unregister(MyUser)
# Now register the new UserAdmin...
admin.site.register(MyUser, UserAdmin)


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

# Unregister the original Group admin.
admin.site.unregister(Group)


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
            self.fieldsets = (
                (None, {'fields': ('translated_name', 'users')}),
            )
            kwargs['fields'] = ('translated_name', 'users')
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

# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)

native_lookup_field = utils.lookup_field


def my_lookup_field(name, obj, model_admin=None):
    logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    logger.debug(str(obj))
    logger.debug(str(model_admin))
    logger.debug('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    if name == 'action_checkbox' \
            and (str(model_admin) == 'auth.GroupAdmin' or str(model_admin) == 'myauth.UserAdmin') \
            and (str(obj) == 'all_users' or str(obj) == 'admins' or str(obj.first_name) == 'Administrador'):
        raise ObjectDoesNotExist
    return native_lookup_field(name, obj, model_admin=model_admin)

utils.lookup_field = my_lookup_field
