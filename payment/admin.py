from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from payment.models import MyPayPalIPN
from payment.forms import MyPayPalIPNForm
from paypal.standard.ipn.models import PayPalIPN
from utils.sites import admin_site
import logging

logger = logging.getLogger('django')


class PaymentAdmin(admin.ModelAdmin):
    form = MyPayPalIPNForm

    def has_add_permission(self, request):
        return False

    list_filter = [
        'payment_status',
        'flag',
        'txn_type',
    ]
    date_hierarchy = 'payment_date'
    fieldsets = (
        (None, {
            "fields": [
                "flag", "txn_id", "txn_type", "payment_status", "payment_date",
                "transaction_entity", "reason_code", "pending_reason",
                "mc_currency", "mc_gross", "mc_fee", "mc_handling", "mc_shipping",
                "auth_status", "auth_amount", "auth_exp", "auth_id"
            ]
        }),
        ("Address", {
            "description": "The address of the Buyer.",
            'classes': ('collapse',),
            "fields": [
                "address_city", "address_country", "address_country_code",
                "address_name", "address_state", "address_status",
                "address_street", "address_zip"
            ]
        }),
        ("Buyer", {
            "description": "The information about the Buyer.",
            'classes': ('collapse',),
            "fields": [
                "first_name", "last_name", "payer_business_name", "payer_email",
                "payer_id", "payer_status", "contact_phone", "residence_country"
            ]
        }),
        ("Seller", {
            "description": "The information about the Seller.",
            'classes': ('collapse',),
            "fields": [
                "business", "item_name", "item_number", "quantity",
                "receiver_email", "receiver_id", "custom", "invoice", "memo"
            ]
        }),
        ("Recurring", {
            "description": "Information about recurring Payments.",
            "classes": ("collapse",),
            "fields": [
                "profile_status", "initial_payment_amount", "amount_per_cycle",
                "outstanding_balance", "period_type", "product_name",
                "product_type", "recurring_payment_id", "receipt_id",
                "next_payment_date"
            ]
        }),
        ("Subscription", {
            "description": "Information about recurring Subscptions.",
            "classes": ("collapse",),
            "fields": [
                "subscr_date", "subscr_effective", "period1", "period2",
                "period3", "amount1", "amount2", "amount3", "mc_amount1",
                "mc_amount2", "mc_amount3", "recurring", "reattempt",
                "retry_at", "recur_times", "username", "password", "subscr_id"
            ]
        }),
        ("Admin", {
            "description": "Additional Info.",
            "classes": ('collapse',),
            "fields": [
                "test_ipn", "ipaddress", "query", "response", "flag_code",
                "flag_info"
            ]
        }),
    )
    # list_display = [
    #     "__unicode__", "flag", "flag_info", "invoice", "custom",
    #     "payment_status", "created_at"
    # ]
    search_fields = ('invoice', 'item_name')
    list_display = ('__unicode__', 'mc_gross', 'payment_status', 'invoice', 'item_name', 'first_name', 'last_name',
                    'payment_date')
    readonly_fields = ('business', 'charset', 'custom', 'notify_version', 'parent_txn_id', 'receiver_email',
                       'receiver_id', 'residence_country', 'test_ipn', 'txn_id', 'txn_type', 'verify_sign',
                       'address_country', 'address_city', 'address_country_code', 'address_name', 'address_state',
                       'address_status', 'address_street', 'address_zip', 'contact_phone', 'first_name', 'last_name',
                       'payer_business_name', 'payer_email', 'payer_id', 'auth_amount', 'auth_exp', 'auth_id',
                       'auth_status', 'exchange_rate', 'invoice', 'item_name', 'item_number', 'mc_currency', 'mc_fee',
                       'mc_gross', 'mc_handling', 'mc_shipping', 'memo', 'num_cart_items', 'option_name1',
                       'option_name2', 'option_selection1', 'option_selection2', 'payer_status', 'payment_date',
                       'payment_gross', 'payment_status', 'payment_type', 'pending_reason', 'protection_eligibility',
                       'quantity', 'reason_code', 'remaining_settle', 'settle_amount', 'settle_currency', 'shipping',
                       'shipping_method', 'tax', 'transaction_entity', 'auction_buyer_id', 'auction_closing_date',
                       'auction_multi_item', 'for_auction', 'amount', 'amount_per_cycle', 'initial_payment_amount',
                       'next_payment_date', 'outstanding_balance', 'payment_cycle', 'period_type', 'product_name',
                       'product_type', 'profile_status', 'recurring_payment_id', 'rp_invoice_id', 'time_created',
                       'amount1', 'amount2', 'amount3', 'mc_amount1', 'mc_amount2', 'mc_amount3', 'password',
                       'period1', 'period2', 'period3', 'reattempt', 'recur_times', 'recurring', 'retry_at',
                       'subscr_date', 'subscr_effective', 'subscr_id',  'username', 'mp_id', 'case_creation_date',
                       'case_id', 'case_type', 'receipt_id', 'currency_code', 'handling_amount', 'transaction_subject',
                       'ipaddress', 'flag', 'flag_code', 'flag_info', 'query', 'response', 'created_at', 'updated_at',
                       'from_view')

admin_site.register(MyPayPalIPN, PaymentAdmin)
