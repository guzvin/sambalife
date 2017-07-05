from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger('django')


class DomainLocaleMiddleware(MiddlewareMixin):
    """
    Set language regarding of domain
    """
    def process_request(self, request):
        logger.debug('==================================================')
        logger.debug(request.META['HTTP_HOST'])
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            # Totally ignore the browser settings...
            logger.debug(request.META['HTTP_ACCEPT_LANGUAGE'])
            del request.META['HTTP_ACCEPT_LANGUAGE']

        current_domain = request.META['HTTP_HOST']
        lang_code = settings.LANGUAGES_DOMAINS.get(current_domain)
        logger.debug(lang_code)
        if lang_code:
            translation.activate(lang_code)
            request.LANGUAGE_CODE = lang_code
            settings.LANGUAGE_CODE = lang_code
