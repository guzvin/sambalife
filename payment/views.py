import json
import logging
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from paypal.standard.models import DEFAULT_ENCODING
from requests.auth import HTTPBasicAuth

from payment.forms import MyPayPalIPNForm
from payment.models import MyPayPalIPN, Subscribe
from payment.templatetags.payments import is_subscriber_voiprime, is_subscriber_wcyazs
from utils import helper
from utils.helper import PaymentException
from .conf import REST_ENDPOINT, SANDBOX_REST_ENDPOINT

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
    token = request.GET.get('token')
    try:
        subscribe = Subscribe.objects.get(execute_agreement_url='/billing-agreements/%s/agreement-execute' % token)
    except Subscribe.DoesNotExist:
        logger.error('Dados invalidos para agreement_return.')
        return HttpResponseServerError()
    if subscribe.is_active:
        return render(request, 'subscriber_return.html', {
            'message': 1
        })
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(subscribe.user)
    subscribe_helper = SubscribeHelper(is_sandbox=is_sandbox, domain=request.CURRENT_DOMAIN)
    try:
        json_response = subscribe_helper.execute_agreement(token)
    except helper.ExecuteAgreementException:
        return HttpResponseServerError()
    if json_response['state'] and json_response['state'].lower() == 'active':
        if subscribe.plan_type == 1:  # Voi Prime
            voi_prime_group = Group.objects.get(name='VoiPrime')
            voi_prime_group.user_set.add(subscribe.user)
            voi_prime_group.save()
            assinantes_group = Group.objects.get(name='Assinantes Lotes')
            assinantes_group.user_set.add(subscribe.user)
            assinantes_group.save()
            texts = (_('Sua assinatura VOI Prime foi realizada com sucesso!'),)
        else:  # We Create Your Amazon Shipment
            wcyazs_group = Group.objects.get(name='We create your AZ Shipment')
            wcyazs_group.user_set.add(subscribe.user)
            wcyazs_group.save()
            texts = (_('Sua assinatura We Create your Amazon Shipment foi realizada com sucesso!'),)
        subscribe.agreement_id = json_response['id']
        subscribe.is_active = True
        subscribe.save(update_fields=['agreement_id', 'is_active'])
        send_email_subscription(request, subscribe.user, _('Confirmação de assinatura'), *texts, async=True)
        return render(request, 'subscriber_return.html', {
            'message': 1
        })
    logger.error('Retorno invalido do execute_agreement.')
    return HttpResponseServerError()


@require_GET
def agreement_cancel(request):
    logger.debug('agreement_cancel nothing to do maybe delete subscribe row')
    logger.debug(str(request.GET.get('token')))
    return render(request, 'subscriber_return.html', {
        'message': 2
    })


@require_POST
@csrf_exempt
def subscription_cancel(request):
    logger.debug('subscription_cancel remove user from groups')
    logger.debug(request.body)

    encoding = request.POST.get('charset', None)

    encoding_missing = encoding is None
    if encoding_missing:
        encoding = DEFAULT_ENCODING

    logger.debug(encoding)
    json_request = json.loads(request.body.decode(encoding))

    try:
        subscribe = Subscribe.objects.get(agreement_id=json_request['resource']['id'])
        if subscribe.plan_type == 1:  # Voi Prime
            voi_prime_group = Group.objects.get(name='VoiPrime')
            voi_prime_group.user_set.remove(subscribe.user)
            voi_prime_group.save()
            assinantes_group = Group.objects.get(name='Assinantes Lotes')
            assinantes_group.user_set.remove(subscribe.user)
            assinantes_group.save()
            texts = (_('Sua assinatura VOI Prime foi cancelada.'),)
        else:  # We Create Your Amazon Shipment
            wcyazs_group = Group.objects.get(name='We create your AZ Shipment')
            wcyazs_group.user_set.remove(subscribe.user)
            wcyazs_group.save()
            texts = (_('Sua assinatura We Create your Amazon Shipment foi cancelada.'),)
        subscribe.is_active = False
        subscribe.save(update_fields=['is_active'])
    except Subscribe.DoesNotExist:
        logger.warning('Dados invalidos para subscription_cancel. agreement_id = %s' % json_request['resource']['id'])
    send_email_subscription(request, subscribe.user, _('Cancelamento de assinatura'), *texts, async=True)
    return HttpResponse('OKAY')


@require_GET
def user_subscribe(request, plan=None):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    if is_subscriber_voiprime(request.user):
        return HttpResponseRedirect(reverse('store'))
    if is_subscriber_wcyazs(request.user):
        return HttpResponseRedirect(reverse('product_stock'))
    is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(request.user)
    subscribe_helper = SubscribeHelper(is_sandbox=is_sandbox, domain=request.CURRENT_DOMAIN)
    try:
        json_response = subscribe_helper.create_agreement(plan)
    except helper.PlanTypeException:
        logger.error('Plano nao encontrado.')
        return HttpResponseBadRequest()
    except helper.CreateAgreementException:
        return HttpResponseServerError()
    links = json_response['links']
    links = links if links is not None else []
    approval_url = None
    execute_agreement_url = None
    for link in links:
        if link['rel'] == 'approval_url':
            approval_url = link['href']
        elif link['rel'] == 'execute':
            execute_agreement_url = link['href']
    if approval_url and execute_agreement_url:
        Subscribe.objects.create(user=request.user,
                                 execute_agreement_url=execute_agreement_url.split('payments')[1],
                                 plan_type=int(plan))
        return HttpResponseRedirect(approval_url)
    logger.error('Link de aprovacao nao encontrado.')
    return HttpResponseServerError()


@login_required
@require_GET
def user_unsubscribe(request, plan=None):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    try:
        subscribe = Subscribe.objects.get(user=request.user, plan_type=int(plan), is_active=True)
    except Subscribe.DoesNotExist:
        logger.error('Usuario nao possui plano contratado.')
        return HttpResponseRedirect(reverse('user_edit'))

    try:
        is_sandbox = settings.PAYPAL_TEST or helper.paypal_mode(request.user)
        subscribe_helper = SubscribeHelper(is_sandbox=is_sandbox, domain=request.CURRENT_DOMAIN)
        subscribe_helper.cancel_agreement(subscribe.agreement_id)
    except helper.CancelAgreementException:
        return HttpResponseServerError()
    return render(request, 'subscriber_return.html', {
        'message': 3
    })


class SubscribeHelper:
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

    def get_plan_id(self, plan_type):
        """Set Sandbox plan if the test variable is present."""
        if self.test_mode():
            if plan_type == '1':
                return settings.PLAN_ID_VOIPRIME_SANDBOX
            return settings.PLAN_ID_WCYAZS_SANDBOX
        else:
            if plan_type == '1':
                return settings.PLAN_ID_VOIPRIME
            return settings.PLAN_ID_WCYAZS

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
                                     headers={'Accept': 'application/json', 'Accept-Language': 'en_US'})
            if response.ok is False:
                logger.error(response.content)
                raise helper.PaypalAccessTokenException()
            response = response.content
            json_response = json.loads(response.decode('utf-8'))
            access_token = json_response['access_token']
            timeout = json_response['expires_in'] * 0.95
            logger.debug('%s ::: %d' % ('timeout', timeout))
            if self.test_mode():
                cache.set('sandbox_access_token', access_token, timeout)
            else:
                cache.set('access_token', access_token, timeout)
        return access_token

    def create_agreement(self, plan=None):
        plan_id = self.get_plan_id(plan)
        if plan == '1':
            agreement_name = _('Acordo VOI PRIME')
            agreement_description = _('Acordo VOI PRIME.')
        elif plan == '2':
            agreement_name = _('Acordo WCYAZS')
            agreement_description = _('Acordo We Create Your Amazon Shipment.')
        else:
            raise helper.PlanTypeException()
        start_date = datetime.utcnow() + timedelta(minutes=5)
        data = {
            'name': agreement_name,
            'description': agreement_description,
            'start_date': '%s%s' % (start_date.replace(microsecond=0).isoformat(), 'Z'),
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
        response = requests.post('%s%s' % (self.get_rest_endpoint(), '/v1/payments/billing-agreements/'),
                                 json=data,
                                 headers={'Accept': 'application/json',
                                          'Authorization': 'Bearer %s' % self.get_rest_access_token()})
        if response.ok is False:
            logger.error(response.content)
            raise helper.CreateAgreementException()
        response = response.content
        logger.debug(response)
        json_response = json.loads(response.decode('utf-8'))
        return json_response

    def execute_agreement(self, token=None):
        response = requests.post('%s/v1/payments/billing-agreements/%s/agreement-execute' % (self.get_rest_endpoint(),
                                                                                             token),
                                 headers={'Accept': 'application/json',
                                          'Content-Type': 'application/json',
                                          'Authorization': 'Bearer %s' % self.get_rest_access_token()})
        if response.ok is False:
            logger.error(response.content)
            raise helper.ExecuteAgreementException()
        response = response.content
        logger.debug(response)
        json_response = json.loads(response.decode('utf-8'))
        return json_response

    def cancel_agreement(self, agreement_id=None):
        # try:
        #     import http.client as http_client
        # except ImportError:
        #     import requests.packages.urllib3.connectionpool as http_client
        # http_client.HTTPConnection.debuglevel = 1
        # requests_log = logging.getLogger("requests.packages.urllib3")

        response = requests.post('%s/v1/payments/billing-agreements/%s/cancel' % (self.get_rest_endpoint(),
                                                                                  agreement_id),
                                 headers={'Accept': 'application/json',
                                          'Content-Type': 'application/json',
                                          'Authorization': 'Bearer %s' % self.get_rest_access_token()})
        logger.debug(response.ok)
        logger.debug(response.status_code)
        if response.ok is False:
            logger.error(response.content)
            raise helper.CancelAgreementException()
        logger.debug(response.content)


def send_email_subscription(request, user, email_title, *texts, async=False):
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>' for x in texts])
    email_body = format_html(html_format, *texts)
    helper.send_email_basic_template_bcc_admins(request, user.first_name, [user.email], email_title,
                                                email_body, async=async)
