from django.utils.translation import ugettext as _
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin
from threading import local
import logging

logger = logging.getLogger('django')
_thread_local = local()


def get_current_request():
    request = getattr(_thread_local, 'request', None)
    if request is None:
        request = HttpRequest()
        request.CURRENT_DOMAIN = 'lots.voiservices.com'
        logger.debug(_('vendedorinternacional.net'))
    return request


def get_current_user():
    request = get_current_request()
    if request:
        return getattr(request, 'user', None)


class ThreadLocalMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        logger.debug('@@@@@@@@@@@@@@@@@ Thread Local Middleware Process Request @@@@@@@@@@@@@@')
        _thread_local.request = request

    @staticmethod
    def process_response(request, response):
        if hasattr(_thread_local, 'request'):
            del _thread_local.request
        return response
