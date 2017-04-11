from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _

from myauth.models import MyUser, UserAddress


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label=_('Senha'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirmação da senha'), widget=forms.PasswordInput)

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
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(UserChangeForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['email'].label = _('E-mail*')
        self.fields['password'].label = _('Senha*')
        self.fields['first_name'].label = _('Nome*')
        self.fields['last_name'].label = _('Sobrenome*')
        self.fields['doc_number'].label = _('CPF*')
        self.fields['cell_phone'].label = _('Celular*')
        self.fields['phone'].required = False

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone', 'is_active',
                  'is_superuser')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


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

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('id', 'email', 'is_superuser', 'is_active',)
    list_display_links = ('id', 'email',)
    list_filter = ('id', 'email', 'is_superuser', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informação pessoal'), {'fields': ('first_name', 'last_name', 'doc_number', 'phone', 'cell_phone',
                                              'is_active',)}),
        (_('Permissões'), {'fields': ('is_superuser',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'doc_number', 'phone', 'cell_phone', 'is_active',
                       'is_superuser', 'password1', 'password2')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

# admin.site.unregister(MyUser)
# Now register the new UserAdmin...
admin.site.register(MyUser, UserAdmin)
