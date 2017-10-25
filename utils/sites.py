from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django import forms
from django.utils.translation import ugettext_lazy as _


class MyAdminAuthenticationForm(AdminAuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class MyAdminSite(AdminSite):
    site_title = _('Vendedor Online Internacional Admin')
    site_header = _('Administração Vendedor Online Internacional')
    login_form = MyAdminAuthenticationForm


admin_site = MyAdminSite(name='admin')
