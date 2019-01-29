# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from sambalife.forms import UserRegistrationForm, UserLoginForm, UserForgotPasswordForm, UserResetPasswordForm
from utils.helper import send_email, send_email_basic_template_bcc_admins, gen_from_key
from utils.models import Params
from django.utils import translation
from django.utils.translation import string_concat, ugettext as _
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.template import loader, Context
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.i18n import set_language
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse, HttpResponseServerError
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from partner.models import Partner
from smtplib import SMTPException
from myauth.models import UserAddress
import socket
import json
import logging

logger = logging.getLogger('django')


@require_GET
@ensure_csrf_cookie
def touch(request):
    return HttpResponse(status=204)


@require_POST
def contact_us(request):
    name = request.POST['name']
    email = request.POST['email']
    tel = request.POST['tel']
    message = request.POST['message']
    if name and email and message:
        try:
            send_email_contact_us(request, name, email, tel, message)
        except (SMTPException, socket.error):
            return HttpResponseServerError()
    else:
        return HttpResponseBadRequest()
    return HttpResponse(json.dumps({'success': True}), content_type='application/json')


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
            username = request.POST['login'].lower()
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if update_user_language(user.id) is False:
                    return HttpResponseBadRequest()
                if 'next' in request.POST:
                    return HttpResponseRedirect(request.POST['next'])
                else:
                    if request.CURRENT_DOMAIN == 'fbaprepmaster.com':
                        return HttpResponseRedirect(reverse('product_stock'))
                    elif request.CURRENT_DOMAIN == 'lots.voiservices.com':
                        return HttpResponseRedirect(reverse('store'))
            else:
                form.add_error(None, _('Não foi possível realizar seu login. Caso tenha esquecido sua senha, '
                                       'clique na opção Esqueci Minha Senha. Em caso de dúvida '
                                       '<a href=\'/pt/ajuda/#contact\'>fale conosco</a>.'))
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
                             'protocol': 'https'}), request)
                str1 = _('Esqueci Senha')
                str2 = _('Vendedor Online Internacional')
                email_tuple = (string_concat(str1, ' - ', str2), message, [user.email])
                send_email((email_tuple,), async=True)
                return render(request, 'login.html', {'success': True, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS})
            else:
                form.add_error(None, _('Conta cadastrada, porém o usuário ainda não foi liberado para acesso '
                                       'ao sistema. Em caso de dúvida '
                                       '<a href=\'/pt/ajuda/#contact\'>fale conosco</a>.'))
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
                    return render(request, 'user_reset_password.html', {'success': True, 'uidb64': uidb64,
                                                                        'token': token})
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
                                           'ao sistema. Em caso de dúvida '
                                           '<a href=\'/pt/ajuda/#contact\'>fale conosco</a>.'))
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
            user.amz_store_name = form.cleaned_data['amz_store_name']
            user.phone = form.cleaned_data['phone']
            user.cell_phone = form.cleaned_data['cell_phone']
            user_password = form.cleaned_data['password']
            user.set_password(user_password)
            if pid:
                try:
                    user.partner = Partner.objects.get(identity=pid)
                except Partner.DoesNotExist:
                    pass
            user.terms_conditions = True
            user.language_code = translation.get_language()
            user.is_active = True
            user.from_key = gen_from_key()
            user.save()
            all_users_group = Group.objects.get(name='all_users')
            all_users_group.user_set.add(user)
            all_users_group.save()
            user_address = UserAddress()
            user_address.user = user
            user_address.address_1 = form.cleaned_data['address_1']
            user_address.address_2 = form.cleaned_data['address_2']
            user_address.country = form.cleaned_data['country']
            user_address.zipcode = form.cleaned_data['zipcode']
            user_address.state = form.cleaned_data['state']
            user_address.city = form.cleaned_data['city']
            user_address.type = 1  # entrega
            user_address.default = True
            user_address.save()

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            # send_validation_email(request, user, uidb64, token)
            user = authenticate(username=user.email, password=user_password)
            if user is None:
                return HttpResponseServerError()
            login(request, user)
            if update_user_language(user.id) is False:
                return HttpResponseBadRequest()
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
                # send_email_user_registration(request, user)
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
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=uid)
            if user.is_verified is False:
                token = default_token_generator.make_token(user)
                send_validation_email(request, user, uidb64, token)
            return render(request, 'user_validation.html', {'success': True,
                                                            'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS})
        except user_model.DoesNotExist:
            return render(request, 'user_validation.html',
                          {'success': False, 'expiry': None, 'uidb64': None})
    return render(request, 'user_validation.html', {'success': False, 'expiry': None, 'uidb64': None})


def send_validation_email(request, user, uid, token):
    ctx = Context({'user_name': user.first_name, 'user_validation_url': 'user_validation', 'uid': uid,
                   'token': token, 'protocol': 'https'})
    message = loader.get_template('email/registration-validation.html').render(ctx, request)
    str1 = _('Cadastro')
    str2 = _('Vendedor Online Internacional')
    email_tuple = (string_concat(str1, ' - ', str2), message, [user.email])
    send_email((email_tuple,), async=True)


def send_email_user_registration(request, user):
    email_title = _('Novo cadastro no sistema')
    html_format = '<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>' \
                  '<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: <strong>{}</strong></p>' \
                  '<p><a href="{}">{}</a> {}</p>'
    texts = (_('Existe um novo cadastro no sistema pendente de ativação.'),
             _('E-mail'), user.email,
             ''.join(['https://', request.CURRENT_DOMAIN, reverse('admin:myauth_myuser_changelist')]),
             _('Clique aqui'), _('para acessar a administração de usuários.'))
    email_body = format_html(html_format, *texts)
    send_email_basic_template_bcc_admins(request, _('Administrador'), None, email_title, email_body)


@login_required
@require_http_methods(["POST"])
def accept_terms_conditions(request):
    user_model = get_user_model()
    try:
        current_user = user_model.objects.get(pk=request.user.id)
        current_user.terms_conditions = True
        current_user.save(update_fields=['terms_conditions'])
        return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
    except user_model.DoesNotExist as e:
        logger.error(e)
        return HttpResponseBadRequest()


def my_set_language(request):
    response = set_language(request)
    if request.user.id is None:
        return response
    if update_user_language(request.user.id) is False:
        return HttpResponseBadRequest()
    return response


def update_user_language(user_id):
    user_model = get_user_model()
    try:
        logger.debug(user_id)
        current_user = user_model.objects.get(pk=user_id)
        current_user.language_code = translation.get_language()
        current_user.save(update_fields=['language_code'])
    except user_model.DoesNotExist as e:
        logger.error(e)
        return False
    return True


# def enviosBrasil(request):
#     return render(request, 'lista_envio_brasil.html')
#
#
#def envioBrasilCadastro(request):
#    return render(request, 'envio_brasil_cadastro.html')
#
#
def envioBrasilDetalhe(request):
    return render(request, 'detalhe_envio_brasil.html')


def how_it_works(request):
    return render(request, 'how_it_works.html')


def help(request):
    return render(request, 'help.html')


def faq(request):
    return render(request, 'faq.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def invoice(request):
    return render(request, 'invoice.html')

def main(request):
    return render(request, 'main.html')

def colab(request):
    if request.method == 'POST':
        texts = (_('Nome'), request.POST.get('collab_name'),
                 _('E-mail'), request.POST.get('collab_email'),
                 _('Telefone'), request.POST.get('collab_phone'),
                 _('Mensagem'), request.POST.get('collab_message'),)
        send_email_collaborator(request, *texts)
        return HttpResponseRedirect('%s?s=1' % reverse('colab'))
    context_data = {}
    if request.GET.get('s') == '1':
        context_data['custom_modal'] = True
        context_data['modal_title'] = _('Colaborador')
        context_data['modal_message'] = _('Formulário enviado com sucesso.')
    return render(request, 'partner.html', context_data)


def send_email_collaborator(request, *texts):
    email_title = _('Formulário novo colaborador')
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}: {}'] * 4)
    email_body = format_html(html_format, *texts)
    send_email_basic_template_bcc_admins(request, _('Administrador'), None, email_title, email_body,
                                         raise_exception=True)


def terms(request):
    return render(request, 'terms.html')


def send_email_contact_us(request, name, email, tel, message, async=False):
    email_title = _('Fale conosco %(user_name)s - Vendedor Online Internacional') % {'user_name': name}
    html_format = '<p>{}: <strong>{}</strong></p>' \
                  '<p>{}: <strong>{}</strong></p>' \
                  '<p>{}: <strong>{}</strong></p>' \
                  '<p>{}: <strong>{}</strong></p>'
    texts = (_('Nome'), name, _('E-mail'), email, _('Telefone'), tel, _('Mensagem'), message)
    email_body = format_html(html_format, *texts)
    ctx = Context({'protocol': 'https', 'email_body': email_body})
    message = loader.get_template('email/contact-us.html').render(ctx, request)
    params = Params.objects.first()
    if params:
        if params.contact_us_mail_to:
            mail_to = params.contact_us_mail_to.split(';')
        else:
            raise Params.DoesNotExist()
    else:
        mail_to = None
    logger.debug(mail_to)
    email_tuple = (email_title, message, mail_to)
    send_email((email_tuple,), bcc_admins=True, async=async, raise_exception=True, reply_to=(email,))
