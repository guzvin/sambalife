from django.utils import translation
from django.utils.translation import string_concat
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import CheckboxInput
from django.forms import BooleanField
from django.forms.formsets import DELETION_FIELD_NAME
from pyparsing import Word, alphas, Literal, CaselessLiteral, Combine, Optional, nums, Or, Forward,\
    ZeroOrMore, StringEnd, alphanums
from django.utils.encoding import smart_str
from django.contrib.auth import get_user_model
from django.template import loader
from django.http import HttpRequest
from smtplib import SMTPException
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_PENDING, ST_PP_VOIDED
from paypal.standard.ipn.signals import valid_ipn_received
from django.utils.html import format_html, mark_safe
from django.utils import formats
from django.utils.encoding import force_text
from django.urls import reverse
from django.db import transaction
from shipment.views import shipment_paypal_notification, shipment_paypal_notification_success
from store.views import store_paypal_notification, store_paypal_notification_success,\
    store_paypal_notification_post_transaction
from django.template import Context, Template
from django.template.base import VariableNode
from utils.models import Params
import threading
import socket
import hashlib
import re
import math
import json
import datetime
import logging

logger = logging.getLogger('django')


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def valida_senha(senha):
    # if senha is None or len(senha) < 6 or \
    #    re.search(r'[a-z]', senha) is None or \
    #    re.search(r'[A-Z]', senha) is None or \
    #    re.search(r'[\d]', senha) is None or \
    #    re.search(r'[^a-zA-Z\d]', senha) is None:
    #     return False
    if senha is None or len(senha) == 0:
        return False
    return True


def digitos(valor):
    return re.sub(r'\D', '', valor)


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


def send_email_basic_template_bcc_admins(request, user_name, user_email, email_title, email_body, async=False):
    ctx = Context({'user_name': user_name, 'protocol': 'https', 'email_body': email_body})
    message = loader.get_template('email/basic-template.html').render(ctx, request)
    str2 = _('Vendedor Online Internacional')
    send_email(string_concat(email_title, ' - ', str2), message, user_email, bcc_admins=True, async=async)


def get_admins_emails():
    user_model = get_user_model()
    admins = user_model.objects.filter(groups__name='admins')
    admins_email = [user.email for user in admins]
    if settings.SYS_SU_USER in admins_email:
        admins_email[admins_email.index(settings.SYS_SU_USER)] = settings.ADMIN_EMAIL
    logger.debug('@@@@@@@@@@@@ ADMINS EMAIL @@@@@@@@@@@@@@')
    logger.debug(admins_email)
    return admins_email


class EmailThread(threading.Thread):
    def __init__(self, title, body, email_from, email_to, bcc, connection):
        self.title = title
        self.body = body
        self.email_from = email_from
        self.email_to = email_to
        self.bcc = bcc
        self.connection = connection
        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMessage(
            self.title,
            self.body,
            from_email=self.email_from,
            to=self.email_to,
            bcc=self.bcc,
            connection=self.connection
        )
        msg.content_subtype = 'html'
        logger.info('@@@@@@@@@@@@ EMAIL MESSAGE @@@@@@@@@@@@@@')
        logger.debug(self.email_from)
        logger.info(self.body)
        try:
            msg.send(fail_silently=False)
        except SMTPException as e:
            try:
                for recipient in e.recipients:
                    logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(recipient))
            except AttributeError:
                pass
            logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(e))
        except socket.error as err:
            logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(err))


def send_email(title, body, email_to=None, email_from=None, bcc_admins=False, async=False):
    if email_from is None:
        email_from = string_concat(_('Vendedor Online Internacional'), ' ',
                                   _('<no-reply@vendedorinternacional.online>'))
    bcc = None
    if bcc_admins:
        bcc = get_admins_emails()

    connection = None
    if translation.get_language() == 'en-us':
        connection = get_connection()
        connection.password = settings.EMAIL_HOST_PASSWORD_EN
        connection.username = settings.EMAIL_HOST_USER_EN
        connection.host = settings.EMAIL_HOST_EN
        connection.port = settings.EMAIL_PORT
        connection.use_tls = settings.EMAIL_USE_TLS
    email = EmailThread(
        title,
        body,
        email_from,
        email_to,
        bcc,
        connection
    )
    if async:
        email.start()
    else:
        email.run()


def resolve_formula(formula, partner=None, reference_date=None):
    template = Template(formula)
    context_var = {}
    for var in template:
        if isinstance(var, VariableNode):
            var = str(var.filter_expression)
            if var == 'partner':
                context_var[var] = str(resolve_partner_value(partner))
            elif var == 'price':
                context_var[var] = str(resolve_price_value(reference_date))
    logger.debug(context_var)
    return template.render(Context(context_var))


def resolve_partner_value(partner):
    if partner:
        if partner.cost:
            return float(partner.cost)
        try:
            return float(Params.objects.first().partner_cost)
        except Params.DoesNotExist:
            pass
    return 0


def resolve_price_value(reference_date):
    try:
        params = Params.objects.first()
    except Params.DoesNotExist:
        return settings.DEFAULT_REDIRECT_FACTOR
    logger.debug('@@@@@@@@@@@@ REFERENCE_DATE @@@@@@@@@@@@@@')
    logger.debug(datetime.datetime.now())
    logger.debug(reference_date)
    if reference_date:
        time_period_one = params.time_period_one
        time_period_two = params.time_period_two
        elapsed = datetime.datetime.now(datetime.timezone.utc) - reference_date
        elapsed = elapsed.days
        logger.debug(elapsed)
        if time_period_one:
            if elapsed <= time_period_one:
                return float(params.redirect_factor)
        if time_period_two:
            if elapsed <= time_period_one + time_period_two:
                return float(params.redirect_factor_two)
            return float(params.redirect_factor_three)
    return float(params.redirect_factor)


class RequiredBaseInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super(RequiredBaseInlineFormSet, self)._construct_form(i, **kwargs)
        form.empty_permitted = True
        return form


class MyBaseInlineFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        self.render_empty_form = kwargs.pop('renderEmptyForm', True)
        self.allow_empty_form = kwargs.pop('allowEmptyForm', True)
        self.novalidate_fields = kwargs.pop('noValidateFields', [])
        self.addText = kwargs.pop('addText', _('Adicionar'))
        self.deleteText = kwargs.pop('deleteText', _('Remover'))
        self.inline_formset_data = json.dumps({
            'name': '#%s' % prefix,
            'options': {
                'prefix': prefix,
                'addText': self.addText,
                'deleteText': self.deleteText,
            }
        })
        super(MyBaseInlineFormSet, self).__init__(data, files, instance, save_as_new, prefix, queryset, **kwargs)

    def __iter__(self):
        """Yields the forms in the order they should be rendered"""
        for form in self.forms:
            yield form
        if self.render_empty_form:
            yield self.empty_form

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        if self.render_empty_form and len(self.forms) == index:
            return self.empty_form
        return self.forms[index]

    def __len__(self):
        if self.render_empty_form:
            return len(self.forms) + 1
        else:
            return len(self.forms)

    def _construct_form(self, i, **kwargs):
        form = super(MyBaseInlineFormSet, self)._construct_form(i, **kwargs)
        if self.allow_empty_form is False:
            form.empty_permitted = False
        return form

    def add_fields(self, form, index):
        super(MyBaseInlineFormSet, self).add_fields(form, index)
        for field in form.fields:
            if field in self.novalidate_fields:
                logger.debug('@@@@@@@@@@@@ NOVALIDATE FORM FIELD @@@@@@@@@@@@@@')
                logger.debug(field)
                form.fields[field].required = False
        if self.can_delete:
            form.fields[DELETION_FIELD_NAME] = BooleanField(label=_('Apagar'), required=False, widget=CheckboxInput)

    def _should_delete_form(self, form):
        form.is_valid()
        return form.cleaned_data.get(DELETION_FIELD_NAME, False)


class Calculate:
    def push_first(self, str, loc, toks):
        self.expr_stack.append(toks[0])

    # def assign_var(self, str, loc, toks):
    #     self.var_stack.append(toks[0])

    def __init__(self):
        self.expr_stack = []
        # self.var_stack = []
        self.variables = {}

        # define grammar
        point = Literal('.')
        e = CaselessLiteral('E')
        plusorminus = Literal('+') | Literal('-')
        number = Word(nums)
        integer = Combine(Optional(plusorminus) + number)
        floatnumber = Combine(integer +
                              Optional(point + Optional(number)) +
                              Optional(e + integer)
                              )
    
        ident = Word(alphas, alphanums + '_')
    
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        # assign = Literal("=")
    
        expr = Forward()
        atom = ((e | floatnumber | integer | ident).setParseAction(self.push_first) |
                (lpar + expr.suppress() + rpar)
                )
    
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor).setParseAction(self.push_first))
    
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + ZeroOrMore((addop + term).setParseAction(self.push_first))
        # bnf = Optional((ident + assign).setParseAction(self.assign_var)) + expr

        # self.pattern = bnf + StringEnd()
        self.pattern = expr + StringEnd()

        # map operator symbols to corresponding arithmetic operations
        self.opn = {
            "+": (lambda a, b: a + b),
            "-": (lambda a, b: a - b),
            "*": (lambda a, b: a * b),
            "/": (lambda a, b: a / b),
            "^": (lambda a, b: a ** b)
        }

    # Recursive function that evaluates the stack
    def evaluate_stack(self, s):
        op = s.pop()
        if op in "+-*/^":
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi
        elif op == "E":
            return math.e
        elif re.search('^[a-zA-Z][a-zA-Z0-9_]*$', op):
            if op in self.variables:
                op = self.variables[op]
            elif 'x' in self.variables:
                op = self.variables['x']
            else:
                return 0
        if re.search('^[-+]?[0-9]+$', str(op)):
            return int(op)
        else:
            return float(op)

    def parse(self, input_string):
        return self.pattern.parseString(input_string)

    def evaluate(self, input_string, variables=None):
        if input_string != '':
            # try parsing the input string
            result_parse = self.parse(input_string)
            # show result of parsing the input string
            logger.debug(' '.join([input_string, '->', str(result_parse)]))
            logger.debug(''.join(['expr_stack=', str(self.expr_stack)]))
            # calculate result , store a copy in ans , display the result to user
            if variables is not None:
                self.variables = variables
            return self.evaluate_stack(self.expr_stack)
        return 0


# Code to override incompatible code from django-paypal module with Python 3
def my_make_secret(form_instance, secret_fields=None):
    secret_fields = ['business', 'item_name']

    data = ""
    for name in secret_fields:
        if hasattr(form_instance, 'cleaned_data'):
            if name in form_instance.cleaned_data:
                data += str(form_instance.cleaned_data[name])
        else:
            # Initial data passed into the constructor overrides defaults.
            if name in form_instance.initial:
                data += str(form_instance.initial[name])
            elif name in form_instance.fields and form_instance.fields[name].initial is not None:
                data += str(form_instance.fields[name].initial)

    secret = get_sha1_hexdigest(settings.SECRET_KEY, data)
    return secret


def get_sha1_hexdigest(salt, raw_password):
    value = smart_str(salt) + smart_str(raw_password)
    hash_sha = hashlib.sha1(value.encode())
    return hash_sha.hexdigest()


class VoidPaymentException(Exception):
    pass


class PaymentException(Exception):
    pass


def paypal_notification(sender, **kwargs):
    ipn_obj, invalid_data, entity, texts, invoice = sender, [], None, None, None
    logger.debug('@@@@@@@@@@@@ PAYPAL NOTIFICATION @@@@@@@@@@@@@@')
    logger.debug(ipn_obj)
    if ipn_obj.test_ipn:
        paypal_business = settings.PAYPAL_BUSINESS_SANDBOX if translation.get_language() == 'pt-br' \
            else settings.PAYPAL_BUSINESS_EN_SANDBOX
    else:
        paypal_business = settings.PAYPAL_BUSINESS if translation.get_language() == 'pt-br' \
            else settings.PAYPAL_BUSINESS_EN
    if ipn_obj.receiver_email != paypal_business:
        # Not a valid payment
        texts = (_('E-mail da conta paypal recebedora não confere com o e-mail configurado no sistema.'),
                 _('E-mail recebido pelo paypal: %(paypal)s') % {'paypal': ipn_obj.receiver_email},
                 _('E-mail configurado no sistema: %(system)s') % {'system': paypal_business})
        invalid_data.append(_html_format(*texts))
    invoice = ipn_obj.invoice.split('_')
    if ipn_obj.invoice is None or (len(invoice) != 3 and len(invoice) != 5) or (invoice[0] != 'A'
                                                                                and invoice[0] != 'B'):
        texts = (_('Valor do campo \'recibo\' (invoice) não está no formato esperado.'),
                 _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice if ipn_obj.invoice is not None
                 else _('<em branco>')})
        invalid_data.append(_html_format(*texts))
    request = HttpRequest()
    request.CURRENT_DOMAIN = sender.current_domain
    try:
        if invalid_data:
            raise PaymentException()
        with transaction.atomic():
            if invoice[0] == 'A':
                entity, texts = shipment_paypal_notification(invoice[1], invoice[2], ipn_obj)
            elif invoice[0] == 'B':
                entity, texts = store_paypal_notification(invoice[1], invoice[2], ipn_obj)
            if entity is None:
                invalid_data.append(_html_format(*texts))
            if entity is not None and (ipn_obj.payment_status == ST_PP_COMPLETED or (invoice[0] == 'B' and
               (ipn_obj.payment_status == ST_PP_PENDING or ipn_obj.payment_status == ST_PP_VOIDED))):
                logger.debug('SUCCESS')
                if invoice[0] == 'A':
                    shipment_paypal_notification_success(request, entity, ipn_obj, _(paypal_status_message(ipn_obj)))
                elif invoice[0] == 'B':
                    store_paypal_notification_success(entity, invoice[1], ipn_obj)
            else:
                logger.info('@@@@@@@@@@@@ PAYMENT STATUS @@@@@@@@@@@@@@')
                raise PaymentException()
        if invoice[0] == 'B':
            store_paypal_notification_post_transaction(request, entity, ipn_obj, _(paypal_status_message(ipn_obj)))
    except PaymentException:
        invalid_data.append(paypal_status_message(ipn_obj))
        admin_url = format_html('<p>{}</p>',
                                mark_safe(_('Para mais informações consulte a área <a href="%(url)s">administrativa'
                                            ' de pagamentos</a>.')
                                          % {'url': ''.join(['https://', request.CURRENT_DOMAIN,
                                                             reverse('admin:payment_mypaypalipn_changelist')])}))
        invalid_data.append(admin_url)
        logger.error('Problema no processamento do retorno do paypal: {0}'.format(invalid_data))
        email_title = _('Informações sobre o pagamento do item \'%(item)s\', recibo %(invoice)s') % \
            {'item': ipn_obj.item_name, 'invoice': ipn_obj.invoice if ipn_obj.invoice is not None else _('<em branco>')}
        email_message = ''.join(invalid_data)
        send_email_basic_template_bcc_admins(request, _('Administrador'), None, email_title, email_message, async=True)
        raise PaymentException()
    except VoidPaymentException:
        ipn_obj.void_authorization()
        email_title = _('\'%(item)s\' indisponível') % {'item': ipn_obj.item_name}
        texts = (_('Foi enviada solicitação para o PayPal cancelar seu pagamento, nenhum valor será cobrado da sua '
                   'conta.'),)
        email_message = _(_html_format(*texts))
        send_email_basic_template_bcc_admins(request, entity.user.first_name, [entity.user.email], email_title,
                                             email_message,  async=True)
        raise PaymentException()


def paypal_status_message(ipn_obj):
    texts = (_('Notificação recebida do paypal.'),
             _('Status: %(status)s') % {'status': ipn_obj.payment_status},
             _('Recibo: %(invoice)s') % {'invoice': ipn_obj.invoice},
             _('Item: %(item)s') % {'item': ipn_obj.item_name},
             _('Nome do cliente: %(name)s') % {'name': ipn_obj.first_name},
             _('Sobrenome do cliente: %(surname)s') % {'surname': ipn_obj.last_name},
             _('Data do pagamento: %(date)s') % {'date': force_text(formats.localize(ipn_obj.payment_date,
                                                                                     use_l10n=True))})
    return _html_format(*texts)


def _html_format(*texts):
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'] +
                          ['<br>{}'] * len(texts[1:]) +
                          ['</p>'])
    return format_html(html_format, *texts)


valid_ipn_received.connect(paypal_notification)
