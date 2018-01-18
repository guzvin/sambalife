from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import ValidationError, MinValueValidator
from django.conf import settings
from django.utils import formats
from django.utils.encoding import force_text
import logging

logger = logging.getLogger('django')


class Params(models.Model):
    id = models.AutoField(primary_key=True)
    contact_us_mail_to = models.CharField(_('E-mail fale conosco'), null=True, blank=True, max_length=500,
                                          help_text=_('Separado por ponto e vírgula.'))
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2, default=0.99)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2, default=0.30)
    fgr_cost = models.DecimalField(_('Valor Repasse'), max_digits=12, decimal_places=2, default=0.20)
    redirect_factor = models.DecimalField(_('Valor Base'), max_digits=12, decimal_places=2, default=1.29)
    time_period_one = models.SmallIntegerField(_('Período Base'), null=True, blank=True,
                                               default=30, help_text=_('Em dias.'),
                                               validators=[MinValueValidator(1)])
    redirect_factor_two = models.DecimalField(_('Valor Pós Período Base'), max_digits=12, decimal_places=2,
                                              null=True, blank=True, default=1.49)
    time_period_two = models.SmallIntegerField(_('Segundo Período'), null=True, blank=True, default=15,
                                               help_text=_('Em dias. Acumulativo com o período base.'),
                                               validators=[MinValueValidator(1)])
    redirect_factor_three = models.DecimalField(_('Valor Pós Segundo Período'), max_digits=12, decimal_places=2,
                                                null=True, blank=True, default=1.99)
    time_period_three = models.SmallIntegerField(_('Terceiro Período'), null=True, blank=True, default=15,
                                                 help_text=_('Em dias. Acumulativo com os períodos anteriores. Após '
                                                             'este período o produto será considerado abandonado.'),
                                                 validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = _('Parametrizações')
        verbose_name_plural = _('Parametrizações')

    def __str__(self):
        return str(_('Parametrizações'))

    def clean(self):
        errors = {}
        logger.debug('@@@@@@@@@@@@ PARAMS CLEAN PREP AND SHIP @@@@@@@@@@@@@@')
        if self.redirect_factor_three is not None:
            if self.time_period_two is None:
                errors['time_period_two'] = ValidationError(_('Quando o campo \'Valor Pós Segundo Período\' está '
                                                              'preenchido, este campo se torna obrigatório.'),
                                                            code='invalid_time_period_two')
            if self.time_period_one is None:
                errors['time_period_one'] = ValidationError(_('Quando o campo \'Valor Pós Segundo Período\' está '
                                                              'preenchido, este campo se torna obrigatório.'),
                                                            code='invalid_time_period_one')
            if self.redirect_factor_two is None:
                errors['redirect_factor_two'] = ValidationError(_('Quando o campo \'Valor Pós Segundo Período\' está '
                                                                  'preenchido, este campo se torna obrigatório.'),
                                                                code='invalid_redirect_factor_two')
            if self.redirect_factor_two and self.redirect_factor_two > self.redirect_factor_three:
                errors['redirect_factor_three'] = self.redirect_factor_three_error_message()
            elif self.redirect_factor > self.redirect_factor_three:
                errors['redirect_factor_three'] = self.redirect_factor_three_error_message()
        if 'redirect_factor_two' not in errors and self.redirect_factor_two is not None:
            if 'time_period_one' not in errors and self.time_period_one is None:
                errors['time_period_one'] = ValidationError(_('Quando o campo \'Valor Pós Período Base\' está '
                                                              'preenchido, este campo se torna obrigatório.'),
                                                            code='invalid_time_period_one')
            if self.redirect_factor > self.redirect_factor_two:
                errors['redirect_factor_two'] = ValidationError(_('Informe um valor maior ou igual a %(price)s.')
                                                                % {'price': self.redirect_factor},
                                                                code='invalid_redirect_factor_two')
        if 'time_period_two' not in errors and self.time_period_two is not None:
            if self.redirect_factor_three is None:
                errors['redirect_factor_three'] = ValidationError(_('Quando o campo \'Segundo Período\' está '
                                                                    'preenchido, este campo se torna obrigatório.'),
                                                                  code='invalid_redirect_factor_three')
            if 'time_period_one' not in errors and self.time_period_one is None:
                errors['time_period_one'] = ValidationError(_('Quando o campo \'Segundo Período\' está preenchido, este'
                                                              ' campo se torna obrigatório.'),
                                                            code='invalid_time_period_one')
            if self.redirect_factor_two is None:
                errors['redirect_factor_two'] = ValidationError(_('Quando o campo \'Segundo Período\' está '
                                                                  'preenchido, este campo se torna obrigatório.'),
                                                                code='invalid_redirect_factor_two')
        if 'time_period_one' not in errors and self.time_period_one is not None:
            if self.redirect_factor_two is None:
                errors['redirect_factor_two'] = ValidationError(_('Quando o campo \'Período Base\' está preenchido, '
                                                                  'este campo se torna obrigatório.'),
                                                                code='invalid_redirect_factor_two')
        if bool(errors):
            raise ValidationError(errors)

    def redirect_factor_three_error_message(self):
        price = self.redirect_factor_two if self.redirect_factor_two and self.redirect_factor_two > 0 and \
                                            self.redirect_factor_two > self.redirect_factor else \
                                            self.redirect_factor
        return ValidationError(_('Informe um valor maior ou igual a %(price)s.') % {'price': price},
                               code='invalid_redirect_factor_three')


class Accounting(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateTimeField(_('Data do Fechamento'), auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_('Usuário'))
    ipaddress = models.GenericIPAddressField(_('Endereço IP'), blank=True, null=True)
    simulation = False

    class Meta:
        verbose_name = _('Fechamento')
        verbose_name_plural = _('Fechamentos')

    def __str__(self):
        return force_text(formats.localize(self.date, use_l10n=True))


class AccountingPartner(models.Model):
    id = models.BigAutoField(primary_key=True)
    partner = models.CharField(_('Sigla Parceiro'), max_length=4)
    value = models.DecimalField(_('Valor USD'), max_digits=12, decimal_places=2)
    paid = models.BooleanField(_('Pago?'), default=False)
    total_products = models.PositiveIntegerField(_('Total de produtos'))
    accounting = models.ForeignKey(Accounting, verbose_name=_('Fechamento'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Parceiro')
        verbose_name_plural = _('Parceiro')

    def __str__(self):
        return str(_('Parceiro'))

    def __iter__(self):
        yield 'id', self.id
        yield 'partner', self.partner
        yield 'value', self.value
        yield 'paid', self.paid
        yield 'total_products', self.total_products
        yield 'accounting', self.accounting


class Billing(models.Model):
    id = models.BigAutoField(primary_key=True)
    TYPE_CHOICES = (
        (1, _('Taxa fixa')),
        (2, _('Por serviços')),
    )
    type = models.SmallIntegerField(_('Tipo'), choices=TYPE_CHOICES, null=True)

    class Meta:
        verbose_name = _('Tipo de cobrança')
        verbose_name_plural = _('Tipo de cobrança')

    def __str__(self):
        if self.type == 1:
            return str(_('Taxa fixa'))
        elif self.type == 2:
            return str(_('Por serviços'))
        return ''
