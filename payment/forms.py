# -*- coding: utf-8 -*-
from paypal.standard.forms import PayPalStandardBaseForm
from paypal.standard.forms import PayPalEncryptedPaymentsForm
from payment.models import MyPayPalIPN
from utils.helper import my_make_secret
from django.conf import settings
import logging

logger = logging.getLogger('django')


class MyPayPalIPNForm(PayPalStandardBaseForm):
    """
    Form used to receive and record PayPal IPN notifications.

    PayPal IPN test tool:
    https://developer.paypal.com/us/cgi-bin/devscr?cmd=_tools-session
    """

    class Meta:
        model = MyPayPalIPN
        exclude = []


class MyPayPalSharedSecretEncryptedPaymentsForm(PayPalEncryptedPaymentsForm):
    def __init__(self, *args, **kwargs):
        self.is_sandbox = kwargs.pop('is_sandbox', False)
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

    def test_mode(self):
        logger.debug('@@@@@@@@@@@@ IS SANDBOX @@@@@@@@@@@@@@')
        logger.debug(self.is_sandbox)
        if self.is_sandbox:
            return True
        return getattr(settings, 'PAYPAL_TEST', True)
