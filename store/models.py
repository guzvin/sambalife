from django.db import models
from django.db.models.fields import BigAutoField
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from store.validators import validate_file_extension
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from utils.storage import OverWriteStorage
from service.models import Service
from PIL import Image
import logging

logger = logging.getLogger('django')

_SAVED_FILEFIELD = 'saved_filefield'
_UNSAVED_FILEFIELD = 'unsaved_filefield'


def lot_directory_path(instance, filename):
    return 'lot_{0}/{1}'.format(instance.id, filename)


class Collaborator(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    email = models.CharField(_('E-mail'), max_length=150)
    address_1 = models.CharField(_('Endereço linha 1'), max_length=60)
    address_2 = models.CharField(_('Endereço linha 2'), max_length=60)
    rating = models.PositiveSmallIntegerField(_('Avaliação'), null=True)

    class Meta:
        verbose_name = _('Colaborador')
        verbose_name_plural = _('Colaboradores')


class Lot(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    description = models.TextField(_('Descrição'), null=True, blank=True)
    STATUS_CHOICES = (
        (1, _('Não vendido')),  # Available
        (2, _('Vendido')),  # Sold
    )
    status = models.SmallIntegerField(_('Situação'), choices=STATUS_CHOICES, default=1)
    payment_complete = models.BooleanField(_('Pago'), default=False)
    create_date = models.DateField(_('Data de Cadastro'), auto_now_add=True)
    sell_date = models.DateTimeField(_('Data da Venda'), null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'Grupos aos quais este lote pertence. Deixe em branco para não restringir o acesso à ele.'
        ),
        related_name="lot_set",
        related_query_name="lot",
    )
    products_quantity = models.IntegerField(_('Quantidade de Produtos'), default=0)
    products_cost = models.DecimalField(_('Custo dos Produtos'), max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(_('Lucro'), max_digits=12, decimal_places=2, default=0)
    average_roi = models.DecimalField(_('ROI Médio'), max_digits=12, decimal_places=2, default=0)
    redirect_cost = models.DecimalField(_('Redirecionamento'), max_digits=12, decimal_places=2, default=0)
    lot_cost = models.DecimalField(_('Valor do Lote'), max_digits=12, decimal_places=2, default=0)
    average_rank = models.DecimalField(_('Rank Médio'), max_digits=12, decimal_places=2, default=0)
    thumbnail = models.ImageField(_('Imagem'), upload_to=lot_directory_path, storage=OverWriteStorage(),
                                  validators=[validate_file_extension], null=True, blank=True)
    voi_cost = models.DecimalField(_('Custo VOI S'), max_digits=12, decimal_places=2, default=0)
    voi_profit = models.DecimalField(_('Lucro VOI S'), max_digits=12, decimal_places=2, default=0)
    voi_roi = models.DecimalField(_('ROI VOI S (%)'), max_digits=12, decimal_places=2, default=0)
    is_archived = models.BooleanField(_('Arquivado'), default=False)
    order_weight = models.IntegerField(_('Peso para ordenação'), default=0)
    is_fake = models.BooleanField('Fake', default=False)
    collaborator = models.ForeignKey(Collaborator, verbose_name=_('Colaborador'), on_delete=models.SET_NULL, null=True,
                                     blank=True)

    class Meta:
        verbose_name = _('Lote')
        verbose_name_plural = _('Lotes')
        permissions = (
            ('view_purchased_lots', _('Pode visualizar lotes comprados')),
        )

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Lot)
def skip_saving_file(sender, instance, **kwargs):
    if instance.thumbnail and not hasattr(instance, _UNSAVED_FILEFIELD) and not hasattr(instance, _SAVED_FILEFIELD):
        setattr(instance, _UNSAVED_FILEFIELD, instance.thumbnail)
        instance.thumbnail = None


@receiver(post_save, sender=Lot)
def save_file(sender, instance, created, **kwargs):
    if hasattr(instance, _UNSAVED_FILEFIELD) and not hasattr(instance, _SAVED_FILEFIELD):
        instance.thumbnail = getattr(instance, _UNSAVED_FILEFIELD)
        delattr(instance, _UNSAVED_FILEFIELD)
        setattr(instance, _SAVED_FILEFIELD, 1)
        instance.save()
        img = Image.open(instance.thumbnail)
        (w, h) = img.size
        if w <= 100 and h <= 100:
            return
        if w > h:
            new_height = round((h / w) * 100)
            size = (100, new_height)
        elif h > w:
            new_width = round((w / h) * 100)
            size = (new_width, 100)
        else:
            size = (100, 100)
        logger.debug(img.size)
        logger.debug('@@@@@@@@@@@@@ THUMB RESIZE @@@@@@@@@@@@@@@@@')
        logger.debug(size)
        img = img.resize(size, Image.ANTIALIAS)
        img.save(instance.thumbnail.path)


class Product(models.Model):
    id = BigAutoField(primary_key=True)
    name = models.CharField(_('Nome'), max_length=150)
    identifier = models.CharField(_('ASIN / UPC'), max_length=50)
    url = models.URLField(_('URL do Produto'), max_length=500, null=True, blank=True)
    buy_price = models.DecimalField(_('Valor de Compra'), max_digits=12, decimal_places=2)
    sell_price = models.DecimalField(_('Valor de Venda'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Quantidade'))
    fba_fee = models.DecimalField(_('Tarifa FBA'), max_digits=12, decimal_places=2)
    amazon_fee = models.DecimalField(_('Tarifa Amazon'), max_digits=12, decimal_places=2,
                                     default=0)
    shipping_cost = models.DecimalField(_('Custo de Envio para Amazon'), max_digits=12, decimal_places=2,
                                        default=settings.DEFAULT_AMAZON_SHIPPING_COST)
    redirect_services = models.ManyToManyField(
        Service,
        verbose_name=_('services'),
        blank=False,
        help_text=_(
            'Serviços utilizados na preparação do envio.'
        ),
        related_name="lot_product_set",
        related_query_name="lot_product",
    )
    product_cost = models.DecimalField(_('Custo do Produto'), max_digits=12, decimal_places=2, default=0)
    profit_per_unit = models.DecimalField(_('Lucro por Unidade'), max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(_('Lucro Total'), max_digits=12, decimal_places=2, default=0)
    roi = models.DecimalField(_('ROI'), max_digits=12, decimal_places=2, default=0)
    rank = models.IntegerField(_('Rank'), default=0)
    voi_value = models.DecimalField(_('Valor item VOI S'), max_digits=12, decimal_places=2, default=0)
    CONDITION_CHOICES = (
        (1, _('New')),
        (2, _('Refurbished')),
        (3, _('Used Like New')),
        (4, _('Used Very Good')),
        (5, _('Used Good')),
        (6, _('Used Acceptable')),
    )
    condition = models.SmallIntegerField(_('Condição'), choices=CONDITION_CHOICES, null=True, blank=False)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')


class Config(models.Model):
    id = models.AutoField(primary_key=True)
    default_group = models.OneToOneField(
        Group,
        verbose_name=_('Grupo padrão'),
        blank=True,
        help_text=_(
            'Grupo ao qual os lotes e os usuários assinantes serão associados por padrão.'
        ),
    )

    class Meta:
        verbose_name = _('Configuração')
        verbose_name_plural = _('Configurações')

    def __str__(self):
        return str(_('Configuração'))


class LotReport(Lot):
    class Meta:
        proxy = True
        verbose_name = _('Relatório')
        verbose_name_plural = _('Relatórios')
