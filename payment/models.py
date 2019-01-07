from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from paypal.standard.ipn.models import PayPalIPN
from .conf import NVP_ENDPOINT, SANDBOX_NVP_ENDPOINT
from django.conf import settings
from utils import helper
import logging
import requests

logger = logging.getLogger('django')


class MyPayPalIPN(PayPalIPN):
    current_domain = ''

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


class Subscribe(models.Model):
    id = BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    agreement_token = models.CharField('Agreement Token', max_length=200)
    agreement_id = models.CharField('Agreement ID', max_length=200, null=True, blank=True)
    PLAN_TYPE_CHOICES = (
        (1, _('VOI Prime')),
        (2, _('We Create Your Amazon Shipment')),
    )
    plan_type = models.SmallIntegerField(_('Tipo de plano'), choices=PLAN_TYPE_CHOICES)
    is_active = models.BooleanField(_('Ativo'), default=False)

    class Meta:
        verbose_name = _('Inscrição')
        verbose_name_plural = _('Inscrições')
