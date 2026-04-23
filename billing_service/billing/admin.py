from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, ClientRateAgreement


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client_name', 'status', 'total_amount', 'balance_due', 'due_date']
    list_filter = ['status']
    search_fields = ['invoice_number', 'client_name']


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'invoice', 'amount', 'method', 'payment_date']
    list_filter = ['method', 'payment_date']


@admin.register(ClientRateAgreement)
class ClientRateAgreementAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'rate_type', 'rate', 'currency', 'is_active']
    list_filter = ['rate_type', 'is_active']
