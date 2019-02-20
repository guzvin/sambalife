import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django')


class DomainMiddleware(MiddlewareMixin):
    """
    Set current domain in request object
    """
    def process_request(self, request):
        request.CURRENT_DOMAIN = request.META['HTTP_HOST']
        # request.CURRENT_DOMAIN = '6c3626c9.ngrok.io'
