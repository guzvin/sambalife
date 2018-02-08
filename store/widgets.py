from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _
import logging

logger = logging.getLogger('django')


class NameTextInput(TextInput):
    def render(self, name, value, attrs=None):
        id_parts = attrs['id'].split('-')
        element_id = ''.join([id_parts[0], '-', id_parts[1], '-clear'])
        attrs['class'] = 'enable-autocomplete-name'
        html = super(NameTextInput, self).render(name, value, attrs)
        return ''.join([html,
                        '&nbsp;<a href="javascript:void(0);" class="selection-clear" id="',
                        element_id,
                        '">(',
                        _('limpar seleção'),
                        ')</a>'])


class IdentifierTextInput(TextInput):
    def render(self, name, value, attrs=None):
        if 'class' in attrs:
            attrs['class'] += ' enable-autocomplete-asin'
        elif attrs:
            attrs['class'] = 'enable-autocomplete-asin'
        else:
            attrs = {'class': 'enable-autocomplete-asin'}
        return super(IdentifierTextInput, self).render(name, value, attrs)
