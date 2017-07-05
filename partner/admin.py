from django.contrib import admin
from .models import Partner


class PartnerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('identity', 'name')}),
    )

admin.site.register(Partner, PartnerAdmin)
