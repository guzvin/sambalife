# -*- coding: utf-8 -*-

from django.shortcuts import render
from sambalife.forms import UserRegistrationForm
from myauth.models import UserAddress
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.conf import settings
from string import Template
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
import os
import codecs
import logging


logger = logging.getLogger('django')


def cadastroLote(request):
    return render(request, 'lote_cadastro.html')

def lotes(request):
    return render(request, 'lista_lotes.html')

def lotesAdmin(request):
    return render(request, 'lista_lotes_admin.html')

def detalheLote(request):
    return render(request, 'detalhe_lote.html')

def login(request):
    return render(request, 'login.html')


def user_registration(request):
    if request.method != 'POST':
        return render(request, 'user_registration.html')
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
            user.doc_number = form.cleaned_data['doc_number']
            user.phone = form.cleaned_data['phone']
            user.cell_phone = form.cleaned_data['cell_phone']
            user.set_password(form.cleaned_data['password'])
            user.save()
            user_address = UserAddress()
            user_address.address_1 = form.cleaned_data['address_1']
            user_address.address_2 = form.cleaned_data['address_2']
            user_address.neighborhood = form.cleaned_data['neighborhood']
            user_address.zipcode = form.cleaned_data['zipcode']
            user_address.state = form.cleaned_data['state']
            user_address.city = form.cleaned_data['city']
            user_address.type = 1  # entrega
            user_address.default = True
            user_address.save()

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            send_validation_email(user, uidb64, token)
            return render(request, 'user_registration.html', {'success': True,
                                                              'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS})
        return render(request, 'user_registration.html', {'form': form, 'success': False, 'status_code': 400},
                      status=400)


def user_validation(request):
    uidb64 = request.GET.get('uidb64')
    token = request.GET.get('token')
    if uidb64 is not None and token is not None:
        uid = urlsafe_base64_decode(uidb64)
        try:
            user_model = get_user_model()
            user = user_model.objects.get(pk=uid)
            if default_token_generator.check_token(user, token) and user.is_active == 0:
                return render(request, 'user_validation.html', {'success': True})
        except:
            pass
    return render(request, 'user_validation.html', {'success': False, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS,
                                                    'uidb64': uidb64})


def user_validation_resend(request):
    uidb64 = request.GET.get('uidb64')
    if uidb64 is not None:
        uid = urlsafe_base64_decode(uidb64)
        try:
            user_model = get_user_model()
            user = user_model.objects.get(pk=uid)
            token = default_token_generator.make_token(user)
            send_validation_email(user, uidb64, token)
        except:
            pass
    return render(request, 'user_validation.html', {'success': False, 'expiry': settings.PASSWORD_RESET_TIMEOUT_DAYS,
                                                    'uidb64': uidb64})


def send_validation_email(user, uid, token):
    with codecs.open(os.path.join(os.path.join(os.path.join(os.path.join(settings.BASE_DIR,
                                                                         'html'),
                                                            'templates'), 'email'), 'registration-email.html'),
                     encoding='utf-8') as registration_email:
        body_string = registration_email.read().replace('\n', '')
        body_template = Template(body_string)
        body_registration = body_template.substitute(arg1=_('Vendedor Online Internacional'),
                                                     arg2=_('Prezado(a) ') + user.first_name,
                                                     arg3=_('Falta apenas esta etapa.'
                                                            ' Clique no botão abaixo para validar seu '
                                                            'cadastro'),
                                                     arg4='https://localhost:9083/user/validation',
                                                     arg5=uid,
                                                     arg6=token,
                                                     arg7=_('VALIDAR CADASTRO'),
                                                     arg8=_('Caso você não tenha feito esta solicitação nos '
                                                            'avise através do e-mail contato@aaaa.com'),
                                                     arg9=_('Este é um e-mail automático disparado pelo '
                                                            'sistema. Favor não respondê-lo, pois esta conta '
                                                            'não é monitorada.')
                                                     )
    send_email(_('Cadastro Vendedor Online Internacional'), body_registration, [user.email])


def pagamentos(request):
    return render(request, 'lista_pagamentos.html')


def pagamentoDetalhe(request):
    return render(request, 'pagamento_detalhe.html')


def estoque(request):
    return render(request, 'estoque.html')


def detalheProduto(request):
    return render(request, 'produto_detalhe.html')


def cadastroProduto(request):
    return render(request, 'produto_cadastro.html')


def shipments(request):
    return render(request, 'lista_shipment.html')


def detalheShipment(request):
    return render(request, 'shipment_detalhe.html')


def cadastroShipment(request):
    return render(request, 'shipment_cadastro.html')


def send_email(title, body, email_to, email_from=_('Vendedor Online Internacional <contato@xxx.com.br>')):
    msg = EmailMessage(
        title,
        body,
        email_from,
        email_to
    )
    msg.content_subtype = 'html'
    msg.send()
