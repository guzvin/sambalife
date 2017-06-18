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
from django.contrib import admin
from django.views.i18n import JavaScriptCatalog
from django.conf.urls.i18n import i18n_patterns
from sambalife.views import *
from product.views import *
from shipment.views import *
from payment.views import *
from store.views import *
from myauth.views import *

urlpatterns = i18n_patterns(
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login[/]$', user_login, name='login'),
    url(r'^logout[/]$', user_logout, name='logout'),
    url(r'^user/password/forgot[/]$', user_forgot_password, name='user_forgot_password'),
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})[/]$',
        user_reset_password, name='user_reset_password'),
    url(r'^user/registration[/]$', user_registration, name='user_registration'),
    url(r'^user/validation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})[/]$',
        user_validation, name='user_validation'),
    url(r'^user/validation/resend/(?P<uidb64>[0-9A-Za-z_\-]+)[/]$', user_validation_resend,
        name='user_validation_resend'),
    url(r'^user/edit[/]$', user_edit, name='user_edit'),
    url(r'^product/stock[/]$', product_stock, name='product_stock'),
    url(r'^product/details/(?P<pid>[0-9]+)[/]$', product_details, name='product_details'),
    url(r'^product/add[/]$', product_add_edit, name='product_add'),
    url(r'^product/edit/(?P<pid>[0-9]+)[/]$', product_add_edit, name='product_edit'),
    url(r'^product/edit/status/(?P<pid>[0-9]+)(?:\.(?P<output>json|html))?', product_edit_status,
        name='product_edit_status'),
    url(r'^product/delete[/]$', product_delete, name='product_delete'),
    url(r'^product/autocomplete[/]$', product_autocomplete, name='product_autocomplete'),
    url(r'^shipment/list[/]$', shipment_list, name='shipment'),
    url(r'^shipment/details/(?P<pid>[0-9]+)[/]$', shipment_details, name='shipment_details'),
    url(r'^shipment/add[/]$', shipment_add, name='shipment_add'),
    url(r'^shipment/calculate[/]$', shipment_calculate, name='shipment_calculate'),
    url(r'^shipment/(?P<pdf>pdf_1)/(?P<pid>[0-9]+)[/]$', shipment_download_pdf, name='shipment_pdf_1'),
    url(r'^shipment/(?P<pdf>pdf_2)/(?P<pid>[0-9]+)[/]$', shipment_download_pdf, name='shipment_pdf_2'),
    url(r'^shipment/delete/product[/]$', shipment_delete_product, name='shipment_delete_product'),
    url(r'^shipment/archive/(?P<pid>[0-9]+)[/]$', shipment_archive, name='shipment_archive'),
    url(r'^paypal/$', payment_ipn, name='paypal-ipn'),
    # url(r'^store/list[/]$', store_list, name='store'),
    # url(r'^store/lot/details/(?P<pid>[0-9]+)[/]$', store_lot_details, name='store_lot_details'),
    # url(r'^store/purchase', store_purchase, name='store_purchase'),
    # url(r'^envios-brasil', enviosBrasil, name='enviosBrasil'),
    # url(r'^envio-brasil/cadastro', envioBrasilCadastro, name='envioBrasilCadastro'),
    # url(r'^envio-brasil/detalhe', envioBrasilDetalhe, name='envioBrasilDetalhe'),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    prefix_default_language=False,
)
