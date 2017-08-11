from django.contrib import admin
from utils.sites import admin_site
from .models import Partner


class PartnerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('identity', 'name')}),
    )

admin_site.register(Partner, PartnerAdmin)
