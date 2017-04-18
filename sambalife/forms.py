from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import ValidationError
from utils.helper import valida_senha


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(label=_('Nome'), max_length=50)
    last_name = forms.CharField(label=_('Sobrenome'), max_length=50)
    email = forms.EmailField(label=_('E-mail'), max_length=150)
    doc_number = forms.CharField(label=_('CPF'), max_length=25)
    phone = forms.CharField(label=_('Telefone'), max_length=25, required=False)
    cell_phone = forms.CharField(label=_('Celular'), max_length=25)
    address_1 = forms.CharField(label=_('Endereço'), max_length=200)
    address_2 = forms.CharField(label=_('Complemento'), max_length=100, required=False)
    neighborhood = forms.CharField(label=_('Bairro'), max_length=100)
    zipcode = forms.CharField(label=_('CEP'), max_length=15)
    state = forms.CharField(label=_('Estado'), max_length=2)
    city = forms.CharField(label=_('Cidade'), max_length=60)
    password = forms.CharField(min_length=6, max_length=30, widget=forms.PasswordInput)
    password_confirmation = forms.CharField(max_length=30, widget=forms.PasswordInput)

    def clean(self):
        password = self.cleaned_data.get('password')
        if password != self.cleaned_data.get('password_confirmation'):
            self.add_error('password_confirmation', ValidationError(_('Informe o mesmo valor'), code='invalid_equal'))

        if not valida_senha(password):
            self.add_error('password', ValidationError(_('Consulte as instruções de formato válido'),
                                                       code='invalid_format'))

        return self.cleaned_data


class UserLoginForm(forms.Form):
    login = forms.CharField(label=_('Login'), max_length=150)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)


class UserForgotPasswordForm(forms.Form):
    login = forms.CharField(label=_('Login'), max_length=150)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput, required=False)


class UserResetPasswordForm(forms.Form):
    email = forms.EmailField(label=_('E-mail'), max_length=150)
    password = forms.CharField(min_length=6, max_length=30, widget=forms.PasswordInput)
    password_confirmation = forms.CharField(max_length=30, widget=forms.PasswordInput)

    def clean(self):
        password = self.cleaned_data.get('password')
        if password != self.cleaned_data.get('password_confirmation'):
            self.add_error('password_confirmation', ValidationError(_('Informe o mesmo valor'), code='invalid_equal'))

        if not valida_senha(password):
            self.add_error('password', ValidationError(_('Consulte as instruções de formato válido'),
                                                       code='invalid_format'))

        return self.cleaned_data
