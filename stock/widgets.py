import logging

from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _

logger = logging.getLogger('django')


class IdentifierTextInput(TextInput):
    def render(self, name, value, attrs=None):
        my_id = attrs['id']
        element_id = ''.join([my_id, '-fill_out'])
        attrs['class'] = 'enable-aws-identifier'
        html = super(IdentifierTextInput, self).render(name, value, attrs)
        return ''.join([html,
                        '&nbsp;<a href="javascript:void(0);" id="',
                        element_id,
                        '">(',
                        _('Preencher cadastro'),
                        ')</a>'])


class UpcTextInput(TextInput):
    def render(self, name, value, attrs=None):
        my_id = attrs['id']
        element_id = ''.join([my_id, '-fill_out'])
        attrs['class'] = 'enable-aws-upc'
        html = super(UpcTextInput, self).render(name, value, attrs)
        return ''.join([html,
                        '&nbsp;<a href="javascript:void(0);" id="',
                        element_id,
                        '">(',
                        _('Preencher cadastro'),
                        ')</a>'])
