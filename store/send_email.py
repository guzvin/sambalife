from django.contrib.auth import get_user_model
from utils.middleware.thread_local import get_current_request
from django.conf import settings
from django.utils import translation
from utils import helper
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger('django')


def email_new_lot_lifecycle(lot):
    email_new_lot(lot, lifecycle=True)


def email_new_lot(lot, lifecycle=False):
    lot_groups = lot.groups.all()
    users_emails_pt = set()
    users_emails_en = set()
    for lot_group in lot_groups:
        uu = get_user_model().objects.filter(is_active=True, groups=lot_group)
        assemble_group_users(users_emails_en, users_emails_pt, uu)
    if users_emails_pt:
        logger.debug(users_emails_pt)
        logger.debug('@@@@@@@@@@@@@@@ NEW LOT USERS NEW LOT USERS NEW LOT USERS PT @@@@@@@@@@@@@@@@@@')
        email_users_new_lot(get_current_request(), lot, users_emails_pt, 'pt', lifecycle=lifecycle)
    if users_emails_en:
        logger.debug(users_emails_en)
        logger.debug('@@@@@@@@@@@@@@@ NEW LOT USERS NEW LOT USERS NEW LOT USERS EN @@@@@@@@@@@@@@@@@@')
        email_users_new_lot(get_current_request(), lot, users_emails_en, 'en', lifecycle=lifecycle)


def assemble_group_users(users_emails_en, users_emails_pt, uu):
    for u in uu:
        if settings.SYS_SU_USER == u.email:
            continue
        if u.language_code == 'pt':
            users_emails_pt.add(u.email)
        else:
            users_emails_en.add(u.email)


def email_users_new_lot(request, lot, users_emails, language_code, lifecycle=False):
    emails = ()
    original_language = translation.get_language()
    if users_emails:
        translation.activate(language_code)
        request.LANGUAGE_CODE = translation.get_language()
        emails += (assemble_email_new_lot(request, lot, lifecycle=lifecycle),)
    translation.activate(original_language)
    if emails:
        helper.send_email(emails, bcc_admins=False, async=True, bcc=users_emails)


def assemble_email_new_lot(request, lot, lifecycle=False):
    email_title = _('Novo lote cadastrado no sistema \'%(lot)s\'') % {'lot': lot.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'] +
                          ['<br>{}'] * 5 +
                          ['</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Lote %(lot_name)s') % {'lot_name': lot.name},
             _('Valor: U$ %(lot_cost)s') % {'lot_cost': helper.force_text(helper.formats.
                                                                          number_format(lot.lot_cost,
                                                                                        use_l10n=True,
                                                                                        decimal_pos=2))},
             _('Lucro: U$ %(lot_profit)s') % {'lot_profit': helper.force_text(helper.formats.
                                                                              number_format(lot.profit,
                                                                                            use_l10n=True,
                                                                                            decimal_pos=2))},
             _('Número de itens: %(lot_items)s') % {'lot_items': lot.products_quantity},
             _('ROI médio: %(lot_roi)s%%') % {'lot_roi': helper.force_text(helper.formats.
                                                                           number_format(lot.average_roi,
                                                                                         use_l10n=True,
                                                                                         decimal_pos=2))},
             _('Rank médio: %(lot_rank)s%%') % {'lot_rank': lot.average_rank})
    texts += (''.join(['https://', request.CURRENT_DOMAIN, helper.reverse('store_lot_details', args=[lot.id])]),
              _('Clique aqui'), _('para acessar este lote agora mesmo!'),)
    if lifecycle:
        if lot.lifecycle == 2:
            texts = (_('FIQUE ATENTO: Este lote será privado para os assinantes somente nas primeiras 24 horas, após '
                       'isto, caso o lote não seja vendido, o mesmo ficará disponível à todos cadastrados na '
                       'plataforma.'), '',) + texts
        elif lot.lifecycle == 4:
            texts = (_('FIQUE ATENTO: Este lote estará disponível à todos cadastrados na plataforma pelas próximas 72 '
                       'horas.'), '',) + texts
    email_body = helper.format_html(html_format, *texts)
    return helper.build_basic_template_email_tuple_bcc(request, email_title, email_body)


def email_lifecycle_lot(lot):
    users_emails_pt = set()
    users_emails_en = set()
    uu = get_user_model().objects.filter(is_active=True)
    assemble_group_users(users_emails_en, users_emails_pt, uu)
    if users_emails_pt:
        logger.debug(users_emails_pt)
        logger.debug('@@@@@@@@@@@ LIFECYCLE LOT USERS LIFECYCLE LOT USERS LIFECYCLE LOT USERS PT @@@@@@@@@@@@@@')
        email_users_lifecycle_lot(get_current_request(), lot, users_emails_pt, 'pt')
    if users_emails_en:
        logger.debug(users_emails_en)
        logger.debug('@@@@@@@@@@@ LIFECYCLE LOT USERS LIFECYCLE LOT USERS LIFECYCLE LOT USERS EN @@@@@@@@@@@@@@')
        email_users_lifecycle_lot(get_current_request(), lot, users_emails_en, 'en')


def email_users_lifecycle_lot(request, lot, users_emails, language_code):
    emails = ()
    original_language = translation.get_language()
    if users_emails:
        translation.activate(language_code)
        request.LANGUAGE_CODE = translation.get_language()
        emails += (assemble_email_lifecycle_lot(request, lot),)
    translation.activate(original_language)
    if emails:
        helper.send_email(emails, bcc_admins=False, async=True, bcc=users_emails)


def assemble_email_lifecycle_lot(request, lot):
    email_title = _('Lote disponível para compra: \'%(lot)s\'') % {'lot': lot.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}'] +
                          ['</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = _('o lote \'%(lot_name)s\' está disponível para ser arrematado por TODOS os usuários da plataforma e '
              'não apenas para os assinantes. Aproveite que em 48 horas este lote será repassado caso ele não seja '
              'arrematado.') % {'lot_name': lot.name},
    texts += (''.join(['https://', request.CURRENT_DOMAIN, helper.reverse('store_lot_details', args=[lot.id])]),
              _('Clique aqui'), _('para acessar este lote agora mesmo!'),)
    email_body = helper.format_html(html_format, *texts)
    return helper.build_basic_template_email_tuple_bcc(request, email_title, email_body)


def email_users_lot_changed(request, lot, users):
    emails = ()
    for user in users:
        emails += (assemble_email_lot_changed(request, lot, user),)
    if emails:
        helper.send_email(emails, bcc_admins=True, async=True)


def assemble_email_lot_changed(request, lot, user):
    email_title = _('Lote alterado \'%(lot)s\'') % {'lot': lot.name}
    html_format = ''.join(['<p style="color:#858585;font:13px/120%% \'Helvetica\'">{}</p>'] +
                          ['<p><a href="{}">{}</a> {}</p>'])
    texts = (_('Este lote sofreu alterações.'),)
    texts += (''.join(['https://', request.CURRENT_DOMAIN, helper.reverse('store_lot_details', args=[lot.id])]),
              _('Clique aqui'), _('para visualizá-las.'),)
    email_body = helper.format_html(html_format, *texts)
    return helper.build_basic_template_email_tuple(request, user.first_name, [user.email], email_title,
                                                   email_body)
