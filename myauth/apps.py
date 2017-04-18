from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MyauthConfig(AppConfig):
    name = 'myauth'
    verbose_name = _('Meus usuários')
