from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from threading import Thread, current_thread
from django.utils.translation import LANGUAGE_SESSION_KEY
import logging

logger = logging.getLogger('django')


class DomainLocaleMiddleware(MiddlewareMixin):
    """
    Set language regarding of domain
    """
    def process_request(self, request):
        logger.debug('==================================================')
        logger.debug(current_thread())
        logger.debug(request.META['HTTP_HOST'])
        # if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        #     # Totally ignore the browser settings...
        #     logger.debug(request.META['HTTP_ACCEPT_LANGUAGE'])
        #     del request.META['HTTP_ACCEPT_LANGUAGE']
        logger.debug(request)
        request.CURRENT_DOMAIN = request.META['HTTP_HOST']
        # lang_code = settings.LANGUAGES_DOMAINS.get(request.CURRENT_DOMAIN)
        # logger.debug(lang_code)
        # if lang_code:
        #     translation.activate(lang_code)
        #     request.LANGUAGE_CODE = translation.get_language()
        logger.debug(translation.get_language())
        request.session[LANGUAGE_SESSION_KEY] = request.LANGUAGE_CODE
        request.CURRENT_DOMAIN = '609bdc8e.ngrok.io'
