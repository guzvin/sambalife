# -*- coding: utf-8 -*-
from django.utils.translation import string_concat
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.conf import settings
import re


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def valida_senha(senha):
    if senha is None or len(senha) < 6 or \
       re.search(r'[a-z]', senha) is None or \
       re.search(r'[A-Z]', senha) is None or \
       re.search(r'[\d]', senha) is None or \
       re.search(r'[^a-zA-Z\d]', senha) is None:
        return False
    return True


def digitos(valor):
    return re.sub(r'\D', '', valor)


def send_email(title, body, email_to, email_from=string_concat(_('Vendedor Online Internacional'), ' ',
                                                               string_concat('<', settings.EMAIL_HOST_USER, '>'))):
    msg = EmailMessage(
        title,
        body,
        email_from,
        email_to,
    )
    msg.content_subtype = 'html'
    msg.send(fail_silently=False)
