# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from paypal.standard.ipn.models import PayPalIPN
from utils.helper import my_make_secret
import logging

logger = logging.getLogger('django')


class MyPayPalIPN(PayPalIPN):
    class Meta:
        proxy = True
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamento')

    def verify_secret(self, form_instance, secret):
        check_secret = my_make_secret(form_instance) == secret
        logger.debug('@@@@@@@@@@@@ CHECK SECRET @@@@@@@@@@@@@@')
        logger.debug(check_secret)
        if not check_secret:
            self.set_flag("Invalid secret. (%s)") % secret
        logger.debug('@@@@@@@@@@@@ PRE SAVE @@@@@@@@@@@@@@')
        self.save()
        logger.debug('@@@@@@@@@@@@ AFTER SAVE @@@@@@@@@@@@@@')