from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, QueryDict
from paypal.standard.models import DEFAULT_ENCODING
from payment.models import MyPayPalIPN
from payment.forms import MyPayPalIPNForm
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
    ipn_obj.send_signals()

    if encoding_missing:
        # Wait until we have an ID to log warning
        logger.warning('No charset passed with PayPalIPN: %s. Guessing %s', ipn_obj.id, encoding)

    return HttpResponse('OKAY')
