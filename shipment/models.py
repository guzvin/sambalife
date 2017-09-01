from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from shipment.validators import validate_file_extension
from datetime import datetime
from product.models import Product as OriginalProduct
from utils import helper
from utils.models import Accounting
from pyparsing import ParseException
import logging

logger = logging.getLogger('django')


_UNSAVED_FILEFIELD = 'unsaved_filefield'


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    if type(instance) is Shipment:
        return 'user_{0}/shipment_{1}/{2}'.format(instance.user.id, instance.id, filename)
    elif type(instance) is Package:
        return 'user_{0}/shipment_{1}/package_{2}/{3}'.format(instance.shipment.user.id, instance.shipment.id,
                                                              instance.id, filename)


class Shipment(models.Model):
    id = BigAutoField(primary_key=True)
    total_products = models.PositiveIntegerField(_('Total de Produtos'))
    cost = models.DecimalField(_('Valor Total'), max_digits=12, decimal_places=2)
    send_date = models.DateField(_('Data de Envio'))
    STATUS_CHOICES = (
        (1, _('Preparando para Envio')),  # Preparing for Shipment
        (2, _('Upload Etiqueta Caixa Autorizado')),  # Upload Box Label Authorized
        (3, _('Pagamento Autorizado')),  # Payment Authorized
        (4, _('Checagens Finais')),  # Final Checkings
        (5, _('Enviado')),  # Shipped
    )
    status = models.SmallIntegerField(_('Status'), choices=STATUS_CHOICES)
    pdf_1 = models.FileField(_('Etiqueta do(s) Produto(s)'), upload_to=user_directory_path,
                             validators=[validate_file_extension])
    is_archived = models.BooleanField(_('Arquivado'), default=False)
    is_canceled = models.BooleanField(_('Cancelado'), default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    accounting = models.ForeignKey(Accounting, verbose_name=_('Fechamento'), on_delete=models.SET_NULL, null=True,
                                   blank=True)
    is_sandbox = models.BooleanField(_('Sandbox'), default=False)

    class Meta:
        verbose_name = _('Envio')
        verbose_name_plural = _('Envios')
        permissions = (
            ('view_shipments', _('Pode visualizar Envios')),
        )

    def clean(self):
        errors = {}
        logger.debug('@@@@@@@@@@@@ SHIPMENT CLEAN DATE @@@@@@@@@@@@@@')
        logger.debug(self.send_date)
        if self.send_date and self.send_date > datetime.now().date():
            errors['send_date'] = ValidationError(_('Informe uma data menor ou igual a de hoje.'), code='invalid_date')
        if bool(errors):
            raise ValidationError(errors)


@receiver(pre_save, sender=Shipment)
def skip_saving_file(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, _UNSAVED_FILEFIELD):
        setattr(instance, _UNSAVED_FILEFIELD, instance.pdf_1)
        instance.pdf_1 = None


@receiver(post_save, sender=Shipment)
def save_file(sender, instance, created, **kwargs):
    if created and hasattr(instance, _UNSAVED_FILEFIELD):
        instance.pdf_1 = getattr(instance, _UNSAVED_FILEFIELD)
        instance.save()


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    product = models.ForeignKey('product.Product')
    receive_date = models.DateTimeField(_('Data de Recebimento'), null=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)
    cost = models.DecimalField(_('Valor de Pagamento'), max_digits=12, decimal_places=2, null=True)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')

    def clean(self):
        errors = {}
        if self.quantity:
            if self.quantity <= 0:
                errors['quantity'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_quantity')
            elif self.product:
                if self.quantity > self.product.quantity_partial:
                    errors['quantity'] = ValidationError(_('Informe um número menor que a quantidade em estoque '
                                                           '(%(quantity)s).')
                                                         % {'quantity': self.product.quantity_partial},
                                                         code='invalid_stock_quantity')
                else:
                    try:
                        original_product = OriginalProduct.objects.get(pk=self.product.id)
                        if self.quantity > original_product.quantity_partial:
                            errors['quantity'] = ValidationError(_('Informe um número menor que a quantidade em '
                                                                   'estoque (%(quantity)s).') %
                                                                 {'quantity': original_product.quantity_partial},
                                                                 code='invalid_stock_quantity')
                    except OriginalProduct.DoesNotExist:
                        errors['quantity'] = ValidationError(_('Problema para validar o produto selecionado.'),
                                                             code='invalid_stock_product')
        if bool(errors):
            raise ValidationError(errors)


class Warehouse(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Warehouse'), max_length=150)
    description = models.TextField(_('Descrição'), null=True, blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)


class Package(models.Model):
    id = BigAutoField(primary_key=True)
    warehouse = models.CharField(_('Warehouse'), max_length=150, null=True)
    weight = models.FloatField(_('Peso'))
    height = models.FloatField(_('H'))
    width = models.FloatField(_('W'))
    length = models.FloatField(_('L'))
    UNITS_WEIGHT_CHOICES = (
        (1, _('Libras'), 'lb.'),  # lbs
        (2, _('Onças'), 'oz'),  # oz
        (3, _('Quilogramas'), 'kg'),  # kg
        (4, _('Gramas'), 'g'),  # g
    )
    weight_units = models.SmallIntegerField(_('Unidade de medida de peso'),
                                            choices=tuple((choice[0], choice[1]) for choice in UNITS_WEIGHT_CHOICES),
                                            default=1)
    UNITS_LENGTH_CHOICES = (
        (1, _('Centímetros'), 'cm'),  # cm
        (2, _('Milímetros'), 'mm'),  # mm
        (3, _('Inches'), '"'),  # '
    )
    length_units = models.SmallIntegerField(_('Unidade de medida de tamanho'),
                                            choices=tuple((choice[0], choice[1]) for choice in UNITS_LENGTH_CHOICES),
                                            default=3)
    pdf_2 = models.FileField(_('Etiqueta da caixa'), upload_to=user_directory_path, null=True,
                             validators=[validate_file_extension])
    shipment_tracking = models.CharField(_('Código UPS'), max_length=50, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)

    __original_warehouse = None
    __original_shipment_tracking = None

    class Meta:
        verbose_name = _('Pacote')
        verbose_name_plural = _('Pacotes')

    def __init__(self, *args, **kwargs):
        super(Package, self).__init__(*args, **kwargs)
        self.__original_warehouse = self.warehouse
        self.__original_shipment_tracking = self.shipment_tracking

    def clean(self):
        errors = {}
        if self.weight and self.weight <= 0:
            errors['weight'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_weight')
        if self.height and self.height <= 0:
            errors['height'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_height')
        if self.width and self.width <= 0:
            errors['width'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_width')
        if self.length and self.length <= 0:
            errors['length'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_length')
        if bool(errors):
            raise ValidationError(errors)


class CostFormula(models.Model):
    id = models.AutoField(primary_key=True)
    formula = models.CharField(_('Fórmula'), max_length=100)

    class Meta:
        verbose_name = _('Cálculo de Envio')
        verbose_name_plural = _('Cálculo de Envio')

    def clean(self):
        try:
            for lang in settings.LANGUAGES:
                helper.Calculate().parse(helper.resolve_formula(self.formula, lang[0]))
        except ParseException as err:
            logger.error(str(err))
            raise ValidationError(_('Fórmula inválida.'), code='invalid_formula')

    def __str__(self):
        return str(_('Fórmula de Envio'))
