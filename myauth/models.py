from django.db import models
from django.db.models.fields import BigAutoField
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _, ugettext
from myauth.my_user_manager import MyUserManager
from django.conf import settings
from django.template import loader, Context
from django.utils import translation
from django.http import HttpRequest
from utils.helper import send_email
from smtplib import SMTPException
from partner.models import Partner
import socket
import logging

logger = logging.getLogger('django')


class MyUser(AbstractBaseUser, PermissionsMixin):
    id = BigAutoField(primary_key=True)
    first_name = models.CharField(_('Nome'), max_length=50)
    last_name = models.CharField(_('Sobrenome'), max_length=50)
    email = models.CharField(_('E-mail'), max_length=150, unique=True)
    doc_number = models.CharField(_('CPF'), max_length=25, null=True)
    cell_phone = models.CharField(_('Telefone 1'), max_length=25)
    phone = models.CharField(_('Telefone 2'), max_length=25, null=True, blank=True)
    date_joined = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    is_active = models.BooleanField(_('Ativo'), default=False)
    is_verified = models.BooleanField(_('Verificado'), default=False)
    partner = models.ForeignKey(Partner, verbose_name=_('Parceiro'), on_delete=models.SET_NULL, null=True, blank=True)
    terms_conditions = models.BooleanField(_('Termos e Condições'), default=False)
    language_code = models.CharField(_('Idioma'), choices=settings.LANGUAGES, max_length=5, default='pt')

    def __iter__(self):
        yield 'id', self.id
        yield 'first_name', self.first_name
        yield 'last_name', self.last_name
        yield 'email', self.email
        yield 'doc_number', self.doc_number
        yield 'phone', self.phone
        yield 'cell_phone', self.cell_phone
        yield 'date_joined', self.date_joined
        yield 'is_active', self.is_active
        yield 'is_verified', self.is_verified
        yield 'partner', self.partner
        yield 'terms_conditions', self.terms_conditions
        yield 'language_code', self.language_code

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'cell_phone']

    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        permissions = (
            ('view_admin', _('Pode visualizar Administração')),
            ('view_users', _('Pode visualizar Usuários')),
        )
        _('Can add')
        _('Can change')
        _('Can delete')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_staff(self):
        return self.is_superuser or self.has_perm('myauth.view_admin')

    def save(self, *args, **kwargs):
        current_language = translation.get_language()
        try:
            if self.pk is not None:
                orig = MyUser.objects.get(pk=self.pk)
                if orig.is_active is False and self.is_active is True:
                    self._send_email('email/account-activation.html')
            elif self.is_active is True:
                self._send_email('email/account-activation.html')
        except SMTPException as e:
            try:
                for recipient in e.recipients:
                    logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(recipient))
            except AttributeError:
                pass
            logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(e))
        except socket.error as err:
            logger.warning('PROBLEMA NO ENVIO DE EMAIL:: %s' % str(err))
        translation.activate(current_language)
        self.email = self.email.lower()
        super(MyUser, self).save(*args, **kwargs)  # Call the "real" save() method

    def _send_email(self, template_name):
        ctx = Context({'user_name': self.first_name, 'protocol': 'https'})
        translation.activate(self.language_code)
        request = HttpRequest()
        request.LANGUAGE_CODE = translation.get_language()
        request.CURRENT_DOMAIN = _('vendedorinternacional.net')
        message = loader.get_template(template_name).render(ctx, request)
        email_tuple = (' - '.join([str(ugettext('Cadastro')), str(ugettext('Vendedor Online Internacional'))]),
                       message,
                       [self.email])
        send_email((email_tuple,), async=True)


class UserAddress(models.Model):
    id = BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    country = models.CharField(_('País'), max_length=2, null=True)
    address_1 = models.CharField(_('Endereço'), max_length=200)
    address_2 = models.CharField(_('Complemento'), max_length=100, null=True)
    zipcode = models.CharField(_('CEP'), max_length=15)
    state = models.CharField(_('Estado'), max_length=100)
    city = models.CharField(_('Cidade'), max_length=60)
    TYPE_CHOICES = (
        (1, _('Entrega')),
        (2, _('Cobrança')),
        (3, _('Entrega e Cobrança')),
    )
    type = models.SmallIntegerField(_('Tipo'), choices=TYPE_CHOICES)  # 1: entrega / 2: cobranca / 3: 1 e 2
    default = models.BooleanField(_('Padrão'))


class UserLotReport(MyUser):
    class Meta:
        proxy = True
        verbose_name = _('Relatório Usuário x Lote')
        verbose_name_plural = _('Relatório Usuário x Lote')
