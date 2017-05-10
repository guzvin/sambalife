# -*- coding: utf-8 -*-
from django.utils.translation import string_concat
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import CheckboxInput
from django.forms import BooleanField
from django.forms.formsets import DELETION_FIELD_NAME
from pyparsing import Word, alphas, Literal, CaselessLiteral, Combine, Optional, nums, Or, Forward, \
    ZeroOrMore, StringEnd, alphanums
from paypal.standard.forms import PayPalEncryptedPaymentsForm
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.forms import PayPalStandardBaseForm
from django.utils.encoding import smart_str
from django.contrib.auth import get_user_model
import hashlib
import re
import math
import json
import logging

logger = logging.getLogger('django')


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


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


def send_email(title, body, email_to=None,
               email_from=string_concat(_('Vendedor Online Internacional'), ' ',
                                        string_concat('<', settings.EMAIL_HOST_USER, '>')), bcc_admins=False):
    bcc = None
    if bcc_admins:
        user_model = get_user_model()
        admins = user_model.objects.filter(groups__name='admins')
        admins_email = [user.email for user in admins]
        if settings.SYS_SU_USER in admins_email:
            admins_email[admins_email.index(settings.SYS_SU_USER)] = settings.ADMIN_EMAIL
        bcc = admins_email
        logger.debug('@@@@@@@@@@@@ ADMINS EMAIL @@@@@@@@@@@@@@')
        logger.debug(admins_email)

    msg = EmailMessage(
        title,
        body,
        from_email=email_from,
        to=email_to,
        bcc=bcc
    )
    msg.content_subtype = 'html'
    msg.send(fail_silently=False)


class MyBaseInlineFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        self.allow_empty_form = kwargs.pop('allowEmptyForm', True)
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
        yield self.empty_form

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        if len(self.forms) == index:
            return self.empty_form
        return self.forms[index]

    def __len__(self):
        return len(self.forms) + 1

    def _construct_form(self, i, **kwargs):
        form = super(MyBaseInlineFormSet, self)._construct_form(i, **kwargs)
        if self.allow_empty_form is False:
            form.empty_permitted = False
        return form

    def add_fields(self, form, index):
        super(MyBaseInlineFormSet, self).add_fields(form, index)
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


class MyPayPalSharedSecretEncryptedPaymentsForm(PayPalEncryptedPaymentsForm):
    def __init__(self, *args, **kwargs):
        super(MyPayPalSharedSecretEncryptedPaymentsForm, self).__init__(*args, **kwargs)
        # @@@ Attach the secret parameter in a way that is safe for other query params.
        secret_param = "?secret=%s" % my_make_secret(self)
        # Initial data used in form construction overrides defaults
        if 'notify_url' in self.initial:
            self.initial['notify_url'] += secret_param
        else:
            self.fields['notify_url'].initial += secret_param

    def _encrypt(self):
        import ewp
        # Iterate through the fields and pull out the ones that have a value.
        plaintext = 'cert_id=%s\n' % self.cert_id
        for name, field in self.fields.items():
            value = None
            if name in self.initial:
                value = self.initial[name]
            elif field.initial is not None:
                value = field.initial
            if value is not None:
                # @@@ Make this less hackish and put it in the widget.
                if name == 'return_url':
                    name = 'return'
                plaintext += '%s=%s\n' % (name, value)
        plaintext = plaintext.encode()

        signature = ewp.sign(self.private_cert, self.public_cert, plaintext)
        ciphertext = ewp.encrypt(self.paypal_cert, signature)
        logger.debug('@@@@@@@@@@@@ PLAINTEXT @@@@@@@@@@@@@@')
        logger.debug(plaintext)
        logger.debug('@@@@@@@@@@@@ SIGNATURE @@@@@@@@@@@@@@')
        logger.debug(signature)
        logger.debug('@@@@@@@@@@@@ CIPHERTEXT @@@@@@@@@@@@@@')
        logger.debug(ciphertext)
        return ciphertext


def get_sha1_hexdigest(salt, raw_password):
    value = smart_str(salt) + smart_str(raw_password)
    hash_sha = hashlib.sha1(value.encode())
    return hash_sha.hexdigest()


class MyPayPalIPN(PayPalIPN):
    class Meta:
        db_table = 'paypal_ipn'
        verbose_name = 'PayPal IPN'

    def verify_secret(self, form_instance, secret):
        check_secret = my_make_secret(form_instance) == secret
        logger.debug('@@@@@@@@@@@@ CHECK SECRET @@@@@@@@@@@@@@')
        logger.debug(check_secret)
        if not check_secret:
            self.set_flag("Invalid secret. (%s)") % secret
        logger.debug('@@@@@@@@@@@@ PRE SAVE @@@@@@@@@@@@@@')
        logger.debug('@@@@@@@@@@@@ CONCRETE FIELDS @@@@@@@@@@@@@@')
        logger.debug(self._meta.concrete_fields)
        logger.debug('@@@@@@@@@@@@ FIELDS @@@@@@@@@@@@@@')
        logger.debug(self._meta.fields)
        for field in self._meta.fields:
            if not field.primary_key:
                logger.debug(field.name)

                if field.name != field.attname:
                    logger.debug(field.attname)
        self.save()
        logger.debug('@@@@@@@@@@@@ AFTER SAVE @@@@@@@@@@@@@@')


class MyPayPalIPNForm(PayPalStandardBaseForm):
    """
    Form used to receive and record PayPal IPN notifications.

    PayPal IPN test tool:
    https://developer.paypal.com/us/cgi-bin/devscr?cmd=_tools-session
    """

    class Meta:
        model = MyPayPalIPN
        exclude = []
