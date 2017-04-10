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

from sambalife.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', login, name='login'),
    url(r'^usuarios/', usuarios, name='usuarios'),
    url(r'^usuario/cadastro/', usuarioCadastro, name='usuarioCadastro'),
    url(r'^usuario/detalhe/', usuarioDetalhe, name='usuarioDetalhe'),
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
]
