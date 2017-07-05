# -*- coding: utf-8 -*-

from django.shortcuts import render
from sambalife.forms import UserRegistrationForm, UserLoginForm, UserForgotPasswordForm, UserResetPasswordForm
from utils.helper import send_email, send_email_basic_template_bcc_admins
from django.utils.translation import string_concat, ugettext as _
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from partner.models import Partner
import logging

logger = logging.getLogger('django')


@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.method == 'GET':
        page_ctx = {}
        if 'next' in request.GET:
            page_ctx = {'next': request.GET['next']}
        return render(request, 'login.html', page_ctx)
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = request.POST['login']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if 'next' in request.POST:
                    return HttpResponseRedirect(request.POST['next'])
                else:
                    return HttpResponseRedirect('/product/stock/')
            else:
                form.add_error(None, _('Não foi possível realizar seu login. Caso tenha esquecido sua senha, '
                                       'clique na opção Esqueci Minha Senha. Em caso de dúvida <a href=\'/#contact\'>'
                                       'fale conosco</a>.'))
        return render(request, 'login.html', {'form': form, 'success': False, 'status_code': 400},
                      status=400)


@require_http_methods(["GET", "POST"])
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@require_POST
def user_forgot_password(request):
    form = UserForgotPasswordForm(request.POST)
    if form.is_valid():
        user_model = get_user_model()
        email = form.cleaned_data['login']
        try:
            user = user_model.objects.get(email=email)
            if user.is_active:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                message = loader.get_template('email/forgot-password.html').render(
                    Context({'user_name': user.first_name, 'uid': uid, 'token': token,
                             'protocol': 'https', 'domain': Site.objects.get_current().domain}))
                str1 = _('Esqueci Senha')
                str2 = _('Vendedor Online Internacional')
                send_email(string_concat(str1, ' - ', str2), message, [user.email])
                return render(request, 'login.html', {'success': True, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS})
            else:
                form.add_error(None, _('Conta cadastrada, porém o usuário ainda não foi liberado para acesso '
                                       'ao sistema. Em caso de dúvida <a href=\'/#contact\'>fale conosco</a>.'))
        except user_model.DoesNotExist:
            form.add_error(None, _('Não foi encontrada conta ativa para este login.'))
    return render(request, 'login.html', {'form': form, 'success': False, 'status_code': 400},
                  status=400)


@require_http_methods(["GET", "POST"])
def user_reset_password(request, uidb64=None, token=None):
    if uidb64 is not None:
        uid = urlsafe_base64_decode(uidb64)
        try:
            user_model = get_user_model()
            user = user_model.objects.get(pk=uid)
            if token is not None and default_token_generator.check_token(user, token):
                if request.method == 'GET':
                    return render(request, 'user_reset_password.html', {'success': True, 'uidb64': uidb64, 'token': token})
                else:
                    form = UserResetPasswordForm(request.POST)
                    if form.is_valid() and user.email == form.cleaned_data['email']:
                        user.set_password(form.cleaned_data['password'])
                        user.save()
                        return render(request, 'user_reset_password.html', {'success': True, 'finish': True})
                    return render(request, 'user_reset_password.html', {'success': False, 'form': form, 'valid': True,
                                                                        'uidb64': uidb64, 'token': token,
                                                                        'status_code': 400}, status=400)
        except user_model.DoesNotExist:
            pass
    return render(request, 'user_reset_password.html', {'success': False, 'valid': False, 'status_code': 400},
                  status=400)


def user_registration(request, pid=None):
    if request.method != 'POST':
        context_data = None
        if request.GET.get('s') == '1':
            context_data = {'success': True, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS}
        return render(request, 'user_registration.html', context_data)
    else:
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user_model = get_user_model()
            email = form.cleaned_data['email']
            try:
                user = user_model.objects.get(email=email)
                if not user.is_active:
                    form.add_error(None, _('E-mail já cadastrado, porém o usuário ainda não foi liberado para acesso '
                                           'ao sistema. Em caso de dúvida <a href=\'/#contact\'>fale conosco</a>.'))
                else:
                    form.add_error(None, _('E-mail já cadastrado, faça o <a href=\'/login\'>login</a> ou, caso '
                                           'tenha esquecido sua senha, <a href=\'/#\'>clique aqui</a>.'))
                return render(request, 'user_registration.html', {'form': form, 'success': False, 'status_code': 400},
                              status=400)
            except user_model.DoesNotExist:
                pass
            user = user_model()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.phone = form.cleaned_data['phone']
            user.cell_phone = form.cleaned_data['cell_phone']
            user.set_password(form.cleaned_data['password'])
            if pid:
                try:
                    user.partner = Partner.objects.get(identity=pid)
                except Partner.DoesNotExist:
                    pass
            user.save()
            all_users_group = Group.objects.get(name='all_users')
            all_users_group.user_set.add(user)
            all_users_group.save()
            # user_address = UserAddress()
            # user_address.user = user
            # user_address.address_1 = form.cleaned_data['address_1']
            # user_address.address_2 = form.cleaned_data['address_2']
            # user_address.country = form.cleaned_data['country']
            # user_address.zipcode = form.cleaned_data['zipcode']
            # user_address.state = form.cleaned_data['state']
            # user_address.city = form.cleaned_data['city']
            # user_address.type = 1  # entrega
            # user_address.default = True
            # user_address.save()

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            send_validation_email(user, uidb64, token)
            if pid:
                return HttpResponseRedirect('%s?s=1' % reverse('user_registration_partner', args=[pid]))
            else:
                return HttpResponseRedirect('%s?s=1' % reverse('user_registration'))
        return render(request, 'user_registration.html', {'form': form, 'success': False, 'status_code': 400},
                      status=400)


def user_validation(request, uidb64=None, token=None):
    if uidb64 is not None:
        uid = urlsafe_base64_decode(uidb64)
        try:
            user_model = get_user_model()
            user = user_model.objects.get(pk=uid)
        except user_model.DoesNotExist:
            return render(request, 'user_validation.html',
                          {'success': False, 'expiry': None, 'uidb64': None})
        if user.is_active is True or user.is_verified is True or \
                (token is not None and default_token_generator.check_token(user, token)):
            if user.is_verified is False:
                user.is_verified = True
                user.is_active = True
                user.save(update_fields=['is_verified', 'is_active'])
                # send_email_user_registration(user)
            return render(request, 'user_validation.html', {'success': True, 'expiry': None,
                                                            'is_active': user.is_active})
        else:
            return render(request, 'user_validation.html',
                          {'success': False, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS,
                           'uidb64': uidb64})
    return render(request, 'user_validation.html', {'success': False, 'expiry': None, 'uidb64': None})


def user_validation_resend(request, uidb64=None):
    if uidb64 is not None:
        uid = urlsafe_base64_decode(uidb64)
        try:
            user_model = get_user_model()
            user = user_model.objects.get(pk=uid)
            if user.is_verified is False:
                token = default_token_generator.make_token(user)
                send_validation_email(user, uidb64, token)
            return render(request, 'user_validation.html', {'success': True,
                                                            'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS})
        except user_model.DoesNotExist:
            return render(request, 'user_validation.html',
                          {'success': False, 'expiry': None, 'uidb64': None})
    return render(request, 'user_validation.html', {'success': False, 'expiry': None, 'uidb64': None})


def send_validation_email(user, uid, token):
    message = loader.get_template('email/registration-validation.html').render(
        Context({'user_name': user.first_name, 'user_validation_url': 'user_validation', 'uid': uid, 'token': token,
                 'protocol': 'https', 'domain': Site.objects.get_current().domain}))
    str1 = _('Cadastro')
    str2 = _('Vendedor Online Internacional')
    send_email(string_concat(str1, ' - ', str2), message, [user.email])


def send_email_user_registration(user):
    email_title = _('Novo cadastro no sistema')
    html_format = '<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>' \
                  '<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: <strong>{}</strong></p>' \
                  '<p><a href="{}">{}</a> {}</p>'
    texts = (_('Existe um novo cadastro no sistema pendente de ativação.'),
             _('E-mail'), user.email,
             ''.join(['https://', Site.objects.get_current().domain, reverse('admin:myauth_myuser_changelist')]),
             _('Clique aqui'), _('para acessar a administração de usuários.'))
    email_body = format_html(html_format, *texts)
    send_email_basic_template_bcc_admins(_('Administrador'), None, email_title, email_body)


def cadastroLote(request):
    return render(request, 'lote_cadastro.html')


def lotes(request):
    return render(request, 'lista_lotes.html')


def lotesAdmin(request):
    return render(request, 'lista_lotes_admin.html')


def detalheLote(request):
    return render(request, 'detalhe_lote.html')

def minhasCompras(request):
    return render(request, 'minhas_compras.html')

def enviosBrasil(request):
    return render(request, 'lista_envio_brasil.html')

def envioBrasilCadastro(request):
    return render(request, 'envio_brasil_cadastro.html')

def envioBrasilDetalhe(request):
    return render(request, 'detalhe_envio_brasil.html')
