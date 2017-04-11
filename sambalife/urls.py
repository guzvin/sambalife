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
from django.conf.urls import url
from django.contrib import admin
from django.views.i18n import JavaScriptCatalog
from django.conf.urls.i18n import i18n_patterns
from sambalife.views import *

urlpatterns = i18n_patterns(
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', login, name='login'),
    url(r'^user/registration/$', user_registration, name='user_registration'),
    url(r'^user/validation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        user_validation, name='user_validation'),
    url(r'^user/validation/resend/(?P<uidb64>[0-9A-Za-z_\-]+)/$', user_validation_resend, name='user_validation_resend'),
    url(r'^pagamentos/', pagamentos, name='pagamentos'),
    url(r'^pagamento/detalhe/', pagamentoDetalhe, name='pagamentoDetalhe'),
    url(r'^estoque/', estoque, name='estoque'),
    url(r'^produtos/detalhe/', detalheProduto, name='detalheProduto'),
    url(r'^produtos/cadastro/', cadastroProduto, name='cadastroProduto'),
    url(r'^shipments/', shipments, name='shipments'),
    url(r'^shipment/detalhe/', detalheShipment, name='detalheShipment'),
    url(r'^shipment/cadastro/', cadastroShipment, name='cadastroShipment'),
    url(r'^lotes/', lotes, name='lotes'),
    url(r'^lote/cadastro/', cadastroLote, name='cadastroLote'),
    url(r'^lotes-admin/', lotesAdmin, name='lotesAdmin'),
    url(r'^lote/detalhe', detalheLote, name='detalheLote'),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    prefix_default_language=False,
)
