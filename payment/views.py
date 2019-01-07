from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from paypal.standard.models import DEFAULT_ENCODING
from payment.models import MyPayPalIPN
from payment.forms import MyPayPalIPNForm
from utils.helper import PaymentException
from requests.auth import HTTPBasicAuth
from django.core.cache import cache
from utils import helper
from django.conf import settings
from .conf import REST_ENDPOINT, SANDBOX_REST_ENDPOINT
import requests
import json
import logging

logger = logging.getLogger('django')

CONTENT_TYPE_ERROR = ("Invalid Content-Type - PayPal is only expected to use "
                      "application/x-www-form-urlencoded. If using django's "
                      "test Client, set `content_type` explicitly")


@require_POST
@csrf_exempt
def payment_ipn(request):
    flag = None
    ipn_obj = None

    # Avoid the RawPostDataException. See original issue for details:
    # https://github.com/spookylukey/django-paypal/issues/79
    if not request.META.get('CONTENT_TYPE', '').startswith(
            'application/x-www-form-urlencoded'):
        raise AssertionError(CONTENT_TYPE_ERROR)

    logger.debug('@@@@@@@@@@@@ PayPal incoming POST data: @@@@@@@@@@@@\n%s', request.body)

    # Clean up the data as PayPal sends some weird values such as "N/A"
    # Also, need to cope with custom encoding, which is stored in the body (!).
    # Assuming the tolerant parsing of QueryDict and an ASCII-like encoding,
    # such as windows-1252, latin1 or UTF8, the following will work:
    encoding = request.POST.get('charset', None)

    encoding_missing = encoding is None
    if encoding_missing:
        encoding = DEFAULT_ENCODING

    try:
        data = QueryDict(request.body, encoding=encoding).copy()
        logger.debug('@@@@@@@@@@@@ PayPal DATA: @@@@@@@@@@@@\n%s', data)
    except LookupError:
        data = None
        flag = 'Invalid form - invalid charset'

    if data is not None:
        if hasattr(MyPayPalIPN._meta, 'get_fields'):
            date_fields = [f.attname for f in MyPayPalIPN._meta.get_fields() if f.__class__.__name__ == 'DateTimeField']
        else:
            date_fields = [f.attname for f, m in MyPayPalIPN._meta.get_fields_with_model()
                           if f.__class__.__name__ == 'DateTimeField']

        for date_field in date_fields:
            if data.get(date_field) == 'N/A':
                del data[date_field]

        form = MyPayPalIPNForm(data)
        if form.is_valid():
            try:
                # When commit = False, object is returned without saving to DB.
                ipn_obj = form.save(commit=False)
            except Exception as e:
                flag = 'Exception while processing. (%s)' % e
        else:
            formatted_form_errors = ['{0}: {1}'.format(k, ', '.join(v)) for k, v in form.errors.items()]
            flag = 'Invalid form. ({0})'.format(', '.join(formatted_form_errors))

    if ipn_obj is None:
        ipn_obj = MyPayPalIPN()

    # Set query params and sender's IP address
    ipn_obj.initialize(request)
    ipn_obj.current_domain = request.CURRENT_DOMAIN

    if flag is not None:
        # We save errors in the flag field
        ipn_obj.set_flag(flag)
    else:
        # Secrets should only be used over SSL.
        if request.is_secure() and 'secret' in request.GET:
            ipn_obj.verify_secret(form, request.GET['secret'])
        else:
            ipn_obj.verify()

    ipn_obj.save()
    try:
        ipn_obj.send_signals()
    except PaymentException:
        logger.debug('==================== ERROR 500 =========================')
        ipn_obj.set_flag('Problem when processing payment.')
        ipn_obj.save(update_fields=['flag', 'flag_info', 'flag_code'])

    if encoding_missing:
        # Wait until we have an ID to log warning
        logger.warning('No charset passed with PayPalIPN: %s. Guessing %s', ipn_obj.id, encoding)

    return HttpResponse('OKAY')


@require_GET
def agreement_return(request):
    logger.debug('agreement_return execute agreement')
    logger.debug(str(request.GET.get('token')))
    # TODO call execute agreement ; add user to groups ; update row in subscribe table to activate
    return HttpResponse('OKAY')


@require_GET
def agreement_cancel(request):
    logger.debug('agreement_cancel nothing to do')
    logger.debug(str(request.GET.get('token')))
    return HttpResponse('OKAY')


@require_POST
@csrf_exempt
def subscription_cancel(request):
    logger.debug('subscription_cancel remove user from groups')
    logger.debug(request.body)
    # TODO remove user from groups ; update row in subscribe table to deactivate
    return HttpResponse('OKAY')


@require_GET
def user_subscribe(request, plan=None):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(request.user)
    subscribe_helper = SubscribeHelper(is_sandbox=is_sandbox, domain=request.CURRENT_DOMAIN)
    try:
        response = subscribe_helper.create_agreement(plan)
    except helper.PlanTypeException:
        return HttpResponseBadRequest()
    json_response = json.loads(response.decode('utf-8'))
    links = json_response['links']
    for link in links:
        if link['rel'] == 'approval_url':
            approval_url = link['href']
            # TODO insert row in subscribe table
            return HttpResponseRedirect(approval_url)
    return HttpResponseServerError()


@login_required
@require_GET
def user_unsubscribe(request, plan=None):
    # TODO call agreement cancellation
    return HttpResponse('OKAY')


class SubscribeHelper():
    def __init__(self, *args, **kwargs):
        self.is_sandbox = kwargs.pop('is_sandbox', False)
        self.domain = kwargs.pop('domain')

    def test_mode(self):
        logger.debug('@@@@@@@@@@@@ IS SANDBOX @@@@@@@@@@@@@@')
        logger.debug(self.is_sandbox)
        if self.is_sandbox:
            return True
        return getattr(settings, 'PAYPAL_TEST', True)

    def get_rest_endpoint(self):
        """Set Sandbox endpoint if the test variable is present."""
        if self.test_mode():
            return SANDBOX_REST_ENDPOINT
        else:
            return REST_ENDPOINT

    def get_rest_access_token(self):
        if self.test_mode():
            access_token = cache.get('sandbox_access_token')
            client_id = settings.PAYPAL_REST_CLIENTID_SANDBOX
            secret = settings.PAYPAL_REST_SECRET_SANDBOX
        else:
            access_token = cache.get('access_token')
            client_id = settings.PAYPAL_REST_CLIENTID
            secret = settings.PAYPAL_REST_SECRET
        if access_token is None:
            response = requests.post('%s%s' % (self.get_rest_endpoint(), '/v1/oauth2/token'),
                                     data={'grant_type': 'client_credentials'},
                                     auth=HTTPBasicAuth(client_id, secret),
                                     headers={'Accept': 'application/json', 'Accept-Language': 'en_US'}).content
            json_response = json.loads(response.decode('utf-8'))
            access_token = json_response['access_token']
            timeout = json_response['expires_in'] - 5
            logger.debug('%s ::: %d' % ('timeout', timeout))
            if self.test_mode():
                cache.set('sandbox_access_token', access_token, timeout)
            else:
                cache.set('access_token', access_token, timeout)
        return access_token

    def create_agreement(self, plan=None):
        if plan == 1:
            plan_id = settings.PLAN_ID_VOIPRIME
            agreement_name = _('Acordo VOI PRIME')
            agreement_description = _('Acordo VOI PRIME.')
        elif plan == 2:
            plan_id = settings.PLAN_ID_WCYAZS
            agreement_name = _('Acordo WCYAZS')
            agreement_description = _('Acordo We Create Your Amazon Shipment.')
        else:
            raise helper.PlanTypeException()
        data = {
            'name': agreement_name,
            'description': agreement_description,
            'start_date': '',
            'payer': {
                'payment_method': 'paypal'
            },
            'plan': {
                'id': plan_id
            },
            'override_merchant_preferences': {
                'return_url': 'https://%s%s' % (self.domain, reverse('paypal-agreement-return')),
                'cancel_url': 'https://%s%s' % (self.domain, reverse('paypal-agreement-cancel')),
                'auto_bill_amount': 'YES',
                'max_fail_attempts': '0'
            }
        }
        response = requests.post('%s%s' % (self.get_rest_endpoint(), '/v1/oauth2/token'),
                                 json=data,
                                 headers={'Accept': 'application/json',
                                          'Authorization': 'Bearer %s' % self.get_rest_access_token()}).content
        return response
