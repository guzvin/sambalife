from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from threading import Thread, current_thread
from django.utils.translation import LANGUAGE_SESSION_KEY
import logging

from django.views.i18n import LANGUAGE_QUERY_PARAMETER

logger = logging.getLogger('django')


class DomainLocaleMiddleware(MiddlewareMixin):
    """
    Set language regarding of domain
    """
    def process_request(self, request):
        logger.debug('==================================================')
        logger.debug(current_thread())
        logger.debug(request.META['HTTP_HOST'])
        #     # Totally ignore the browser settings...
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']
        logger.debug(request)
        request.CURRENT_DOMAIN = request.META['HTTP_HOST']
        lang_code = request.POST.get(LANGUAGE_QUERY_PARAMETER)
        # lang_code = settings.LANGUAGES_DOMAINS.get(request.CURRENT_DOMAIN)
        logger.debug(lang_code)
        if lang_code:
            translation.activate(lang_code)
            request.LANGUAGE_CODE = translation.get_language()
        logger.debug(translation.get_language())
        request.session[LANGUAGE_SESSION_KEY] = request.LANGUAGE_CODE
        # request.CURRENT_DOMAIN = '6c3626c9.ngrok.io'
