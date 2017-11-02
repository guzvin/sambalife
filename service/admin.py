from utils.sites import admin_site
from service.models import Service, Config
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price',)

admin_site.register(Service, ServiceAdmin)


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('translated_name',)

    def translated_name(self, obj):
        return _('Configuração')

    translated_name.short_description = _('Configuração')

    def has_add_permission(self, request):
        if request.user.is_authenticated:
            formula_exists = Config.objects.all().count() == 1
            if formula_exists is False:
                return super(ConfigAdmin, self).has_add_permission(request)
        return False

admin_site.register(Config, ConfigAdmin)
