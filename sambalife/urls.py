"""sambalife URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from utils.sites import admin_site
from django.views.i18n import JavaScriptCatalog
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import ugettext_lazy as _
from sambalife.views import *
from product.views import *
from shipment.views import *
from payment.views import *
from store.views import *
from service.views import *
from utils.views import *
from myauth.views import *

urlpatterns = [
    url(r'^paypal/$', payment_ipn, name='paypal-ipn'),
    url(r'^paypal/agreement/return/$', agreement_return, name='paypal-agreement-return'),
    url(r'^paypal/agreement/cancel/$', agreement_cancel, name='paypal-agreement-cancel'),
    url(r'^paypal/subscription/cancel/$', subscription_cancel, name='paypal-subscription-cancel'),
    url(r'^i18n/setlang/', my_set_language, name='my_set_language'),
    # url(r'^i18n/', include('django.conf.urls.i18n')),
]
urlpatterns += i18n_patterns(
    url(r'^admin/', include(admin_site.urls)),
    url(r'^admin/close_accounting/$', close_accounting, name='close_accounting'),
    url(r'^admin/close_accounting_sandbox/$', close_accounting_sandbox, name='close_accounting_sandbox'),
    url(_(r'^login[/]$'), user_login, name='login'),
    url(_(r'^logout[/]$'), user_logout, name='logout'),
    url(_(r'^user/password/forgot[/]$'), user_forgot_password, name='user_forgot_password'),
    url(_(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})[/]$'),
        user_reset_password, name='user_reset_password'),
    url(_(r'^user/registration[/]$'), user_registration, name='user_registration'),
    url(_(r'^user/(?P<pid>[0-9A-Za-z]{4})/registration[/]$'), user_registration, name='user_registration_partner'),
    url(_(r'^user/validation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})[/]$'),
        user_validation, name='user_validation'),
    url(_(r'^user/validation/resend/(?P<uidb64>[0-9A-Za-z_\-]+)[/]$'), user_validation_resend,
        name='user_validation_resend'),
    url(_(r'^user/edit[/]$'), user_edit, name='user_edit'),
    url(_(r'^product/stock[/]$'), product_stock, name='product_stock'),
    url(_(r'^product/stock/merchant[/]$'), product_stock_fbm, name='product_stock_fbm'),
    url(_(r'^product/details/(?P<pid>[0-9]+)[/]$'), product_details, name='product_details'),
    url(_(r'^product/add[/]$'), product_add_edit, name='product_add'),
    url(_(r'^product/edit/(?P<pid>[0-9]+)[/]$'), product_add_edit, name='product_edit'),
    url(_(r'^product/delete[/]$'), product_delete, name='product_delete'),
    url(_(r'^shipment/list[/]$'), shipment_list, name='shipment'),
    url(_(r'^shipment/details/(?P<pid>[0-9]+)[/]$'), shipment_details, name='shipment_details'),
    url(_(r'^shipment/add[/]$'), shipment_add, name='shipment_add'),
    url(_(r'^shipment/create[/]$'), shipment_add_fba_prep, name='shipment_create'),
    url(r'^shipment/(?P<pdf>pdf_1)/(?P<pid>[0-9]+)[/]$', shipment_download_pdf, name='shipment_pdf_1'),
    url(r'^shipment/(?P<pdf>pdf_2)/(?P<pid>[0-9]+)[/]$', shipment_download_pdf, name='shipment_pdf_2'),
    url(r'^shipment/standby/(?P<pid>[0-9]+)/(?P<op>(1|2)+)[/]$', shipment_standby, name='shipment_standby'),
    url(r'^shipment/archive/(?P<pid>[0-9]+)/(?P<op>(1|2)+)[/]$', shipment_archive, name='shipment_archive'),
    url(r'^shipment/cancel/(?P<pid>[0-9]+)[/]$', shipment_cancel, name='shipment_cancel'),
    url(r'^shipment/status/(?P<pid>[0-9]+)/(?P<op>(forward|backward)+)[/]$', shipment_status, name='shipment_status'),
    url(_(r'^mf_shipment/list[/]$'), merchant_shipment_list, name='merchant_shipment'),
    url(_(r'^mf_shipment/add[/]$'), merchant_shipment_add, name='merchant_shipment_add'),
    url(_(r'^store/list[/]$'), store_list, name='store'),
    url(_(r'^store/lot/details/(?P<pid>[0-9]+)[/]$'), store_lot_details, name='store_lot_details'),
    url(_(r'^store/lot/invoice/(?P<pid>[0-9]+)[/]$'), store_lot_invoice, name='store_lot_invoice'),
    url(_(r'^store/purchase'), store_purchase, name='store_purchase'),
    url(r'^store/pay/(?P<pid>[0-9]+)[/]$', store_pay_form, name='store_pay_form'),
    #url(r'^envios-brasil', enviosBrasil, name='enviosBrasil'),
    #url(r'^envio-brasil/cadastro', envioBrasilCadastro, name='envioBrasilCadastro'),
    #url(r'^envio-brasil/detalhe', envioBrasilDetalhe, name='envioBrasilDetalhe'),
    url(r'^purchase/invoice', invoice, name='invoice'),
    url(r'^touch/$', touch, name='touch'),
    url(r'^contactus/$', contact_us, name='contactus'),
    url(r'^product/edit/status/(?P<pid>[0-9]+)(?:\.(?P<output>json|html))?', product_edit_status,
        name='product_edit_status'),
    url(r'^shipment/delete/product.(?P<output>json)[/]$', shipment_delete_product, name='shipment_delete_product'),
    url(r'^shipment/pay/(?P<pid>[0-9]+)[/]$', shipment_pay_form, name='shipment_pay_form'),
    url(r'^shipment/calculate[/]$', shipment_calculate, name='shipment_calculate'),
    url(r'^user/accept_terms[/]$', accept_terms_conditions, name='accept_terms_conditions'),
    url(r'^user/amz_store_name[/]$', user_amz_store_name, name='user_amz_store_name'),
    url(r'^user/impersonate[/]$', user_impersonate, name='user_impersonate'),
    url(r'^user/end_impersonate[/]$', user_end_impersonate, name='user_end_impersonate'),
    url(r'^user/subscribe/(?P<plan>[1-2]{1})[/]$', user_subscribe, name='user_subscribe'),
    url(r'^user/unsubscribe/(?P<plan>[1-2]{1})[/]$', user_unsubscribe, name='user_unsubscribe'),
    url(r'^product/autocomplete[/]$', product_autocomplete, name='product_autocomplete'),
    url(r'^product/autocomplete/merchant[/]$', product_autocomplete_fbm, name='product_autocomplete_fbm'),
    url(r'^service/product/(?P<pid>[0-9]+)[/]$', service_product, name='service_product'),
    url(r'^service/shipment/(?P<sid>[0-9]+)[/]$', service_shipment, name='service_shipment'),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url(_(r'^how-it-works'), how_it_works, name='how_it_works'),
    url(r'^ajuda', help, name='help'),
    url(r'^faq', faq, name='faq'),
    url(_(r'^seja-um-colaborador'), colab, name='colab'),
    url(_(r'^termos-e-condicoes-de-uso'), terms, name='terms'),
    url(_(r'^politicas-de-privacidade'), privacy_policy, name='privacy_policy'),
    url(r'^store/product_name/autocomplete[/]$', product_name_autocomplete, name='store_product_name_autocomplete'),
    url(r'^store/product_asin/autocomplete[/]$', product_asin_autocomplete, name='store_product_asin_autocomplete'),
    url(r'^store/product_upc/autocomplete[/]$', product_upc_autocomplete, name='store_product_upc_autocomplete'),
    url(r'^store/public_countdown/(?P<pid>[0-9]+)/$', public_countdown, name='public_countdown'),
)
