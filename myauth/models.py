from django.db import models
from django.db.models.fields import BigAutoField
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from myauth.my_user_manager import MyUserManager
from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site
from utils.helper import send_email


class MyUser(AbstractBaseUser, PermissionsMixin):
    id = BigAutoField(primary_key=True)
    first_name = models.CharField(_('Nome'), max_length=50)
    last_name = models.CharField(_('Sobrenome'), max_length=50)
    email = models.CharField(_('E-mail'), max_length=150, unique=True)
    doc_number = models.CharField(_('CPF'), max_length=25)
    phone = models.CharField(_('Telefone'), max_length=25, null=True)
    cell_phone = models.CharField(_('Celular'), max_length=25)
    date_joined = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    is_active = models.BooleanField(_('Ativo'), default=False)
    is_verified = models.BooleanField(_('Verificado'), default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'doc_number', 'cell_phone']

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
        if self.pk is not None:
            orig = MyUser.objects.get(pk=self.pk)
            if orig.is_active is False and self.is_active is True:
                self._send_email('email/account-activation.html')
        elif self.is_active is True:
            self._send_email('email/account-activation.html')
        super(MyUser, self).save(*args, **kwargs)  # Call the "real" save() method

    def _send_email(self, template_name):
        message = loader.get_template(template_name).render(
            Context({'user_name': self.first_name, 'protocol': 'https',
                     'domain': Site.objects.get_current().domain}))
        str1 = _('Cadastro')
        str2 = _('Vendedor Online Internacional')
        send_email(string_concat(str1, ' ', str2), message, [self.email])


class UserAddress(models.Model):
    id = BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_1 = models.CharField(_('Endereço'), max_length=200)
    address_2 = models.CharField(_('Complemento'), max_length=100, null=True)
    neighborhood = models.CharField(_('Bairro'), max_length=100)
    zipcode = models.CharField(_('CEP'), max_length=15)
    state = models.CharField(_('Estado'), max_length=2)
    city = models.CharField(_('Cidade'), max_length=60)
    TYPE_CHOICES = (
        (1, _('Entrega')),
        (2, _('Cobrança')),
        (3, _('Entrega e Cobrança')),
    )
    type = models.SmallIntegerField(_('Tipo'), choices=TYPE_CHOICES)  # 1: entrega / 2: cobranca / 3: 1 e 2
    default = models.BooleanField(_('Padrão'))
