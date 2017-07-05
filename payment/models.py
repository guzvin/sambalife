from django.utils.translation import ugettext_lazy as _
from paypal.standard.ipn.models import PayPalIPN
from .conf import NVP_ENDPOINT, SANDBOX_NVP_ENDPOINT
from django.conf import settings
from utils import helper
import logging
import requests

logger = logging.getLogger('django')


class MyPayPalIPN(PayPalIPN):
    class Meta:
        proxy = True
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamento')

    def verify_secret(self, form_instance, secret):
        check_secret = helper.my_make_secret(form_instance) == secret
        logger.debug('@@@@@@@@@@@@ CHECK SECRET @@@@@@@@@@@@@@')
        logger.debug(check_secret)
        if not check_secret:
            self.set_flag("Invalid secret. (%s)") % secret
        logger.debug('@@@@@@@@@@@@ PRE SAVE @@@@@@@@@@@@@@')
        self.save()
        logger.debug('@@@@@@@@@@@@ AFTER SAVE @@@@@@@@@@@@@@')

    def get_nvp_endpoint(self):
        """Set Sandbox endpoint if the test variable is present."""
        if self.test_ipn:
            return SANDBOX_NVP_ENDPOINT
        else:
            return NVP_ENDPOINT

    def get_nvp_auth_data(self):
        if self.test_ipn:
            data = {'USER': settings.PAYPAL_NVP_USER_SANDBOX, 'PWD': settings.PAYPAL_NVP_PWD_SANDBOX,
                    'SIGNATURE': settings.PAYPAL_NVP_SIGNATURE_SANDBOX}
        else:
            data = {'USER': settings.PAYPAL_NVP_USER, 'PWD': settings.PAYPAL_NVP_PWD,
                    'SIGNATURE': settings.PAYPAL_NVP_SIGNATURE}
        data['VERSION'] = '94.0'
        return data

    def complete_authorization(self):
        data = self.get_nvp_auth_data()
        data['METHOD'] = 'DoCapture'
        data['AUTHORIZATIONID'] = self.auth_id
        data['NOTE'] = _('Compra confirmada.')
        data['AMT'] = self.auth_amount
        data['COMPLETETYPE'] = 'Complete'
        data['INVNUM'] = self.invoice
        return requests.post(self.get_nvp_endpoint(), data=data).content

    def void_authorization(self):
        data = self.get_nvp_auth_data()
        data['METHOD'] = 'DoVoid'
        data['AUTHORIZATIONID'] = self.auth_id
        data['NOTE'] = _('Compra cancelada por indisponibilidade do produto.')
        # data['MSGSUBID'] = ''
        return requests.post(self.get_nvp_endpoint(), data=data).content
