from django.db import models
from django.db.models.fields import BigAutoField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import ValidationError
from shipment.validators import validate_file_extension
from datetime import datetime
from product.models import Product as OriginalProduct
from utils.helper import Calculate
from pyparsing import ParseException
import logging

logger = logging.getLogger('django')


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Shipment(models.Model):
    id = BigAutoField(primary_key=True)
    total_products = models.FloatField(_('Total de Produtos'))
    cost = models.DecimalField(_('Valor Total'), max_digits=12, decimal_places=2)
    send_date = models.DateField(_('Data de Envio'))
    STATUS_CHOICES = (
        (1, _('Preparando para Envio')),  # Preparing for Shipment
        (2, _('Pagamento Autorizado')),  # Payment Authorized
        (3, _('Upload PDF 2 Autorizado')),  # Upload PDF 2 Authorized
        (4, _('Checagens Finais')),  # Final Checkings
        (5, _('Enviado')),  # Shipped
    )
    status = models.SmallIntegerField(_('Status'), choices=STATUS_CHOICES)
    pdf_1 = models.FileField(_('PDF 1'), upload_to=user_directory_path, validators=[validate_file_extension])
    pdf_2 = models.FileField(_('PDF 2'), upload_to=user_directory_path, null=True, blank=True,
                             validators=[validate_file_extension])
    shipment = models.FileField(_('Comprovante de Envio'), upload_to=user_directory_path, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    quantity = models.FloatField(_('Quantidade'))
    product = models.ForeignKey(OriginalProduct, on_delete=models.CASCADE)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')

    def clean(self):
        errors = {}
        if self.quantity:
            if self.quantity <= 0:
                errors['quantity'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_quantity')
            elif self.product:
                if self.quantity > self.product.quantity:
                    errors['quantity'] = ValidationError(_('Informe um número menor que a quantidade em estoque '
                                                           '(%(quantity)s).') % {'quantity': self.product.quantity},
                                                         code='invalid_stock_quantity')
                else:
                    try:
                        original_product = OriginalProduct.objects.get(pk=self.product.id)
                        if self.quantity > original_product.quantity:
                            errors['quantity'] = ValidationError(_('Informe um número menor que a quantidade em '
                                                                   'estoque (%(quantity)s).') %
                                                                 {'quantity': original_product.quantity},
                                                                 code='invalid_stock_quantity')
                    except OriginalProduct.DoesNotExist:
                        errors['quantity'] = ValidationError(_('Problema para validar o produto selecionado.'),
                                                             code='invalid_stock_product')
        if bool(errors):
            raise ValidationError(errors)


class Package(models.Model):
    id = BigAutoField(primary_key=True)
    weight = models.FloatField(_('Peso'))
    height = models.FloatField(_('Altura'))
    width = models.FloatField(_('Largura'))
    depth = models.FloatField(_('Profundidade'))
    UNITS_WEIGHT_CHOICES = (
        (1, _('Pound')),  # lbs
        (2, _('Ounce')),  # oz
        (3, _('Quilograma')),  # kg
        (4, _('Grama')),  # g
    )
    weight_units = models.SmallIntegerField(_('Unidade de medida de peso'), choices=UNITS_WEIGHT_CHOICES, default=1)
    UNITS_LENGTH_CHOICES = (
        (1, _('Centímetro')),  # cm
        (2, _('Milímetro')),  # mm
        (3, _('Inch')),  # '
    )
    length_units = models.SmallIntegerField(_('Unidade de medida de tamanho'), choices=UNITS_LENGTH_CHOICES, default=1)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Pacote')
        verbose_name_plural = _('Pacotes')

    def clean(self):
        errors = {}
        if self.weight and self.weight <= 0:
            errors['weight'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_weight')
        if self.height and self.height <= 0:
            errors['height'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_height')
        if self.width and self.width <= 0:
            errors['width'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_width')
        if self.depth and self.depth <= 0:
            errors['depth'] = ValidationError(_('Informe um número maior que zero.'), code='invalid_depth')
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
            Calculate().parse(self.formula)
        except ParseException as err:
            logger.error(str(err))
            raise ValidationError(_('Fórmula inválida.'), code='invalid_formula')

    def __str__(self):
        return str(_('Fórmula de Envio'))
