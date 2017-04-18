from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import ValidationError
from datetime import datetime
import logging

logger = logging.getLogger('django')


class ProductForm(forms.Form):
    name = forms.CharField(label=_('Nome'), max_length=150)
    description = forms.CharField(label=_('Descrição'), required=False)
    quantity = forms.FloatField(label=_('Quantidade'))
    send_date = forms.DateField(label=_('Data Envio'), localize=True)

    def clean(self):
        send_date = self.cleaned_data.get('send_date')
        if send_date and send_date > datetime.now().date():
            self.add_error('send_date', ValidationError(_('Informe uma data menor ou igual a de hoje.'),
                                                        code='invalid_date'))
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            self.add_error('quantity', ValidationError(_('Informe um número maior que zero.'),
                                                       code='invalid_quantity'))
        return self.cleaned_data
