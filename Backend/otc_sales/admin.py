from django.contrib import admin
from .models import Transaction, TransactionItem

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'payment_method', 'grand_total', 'sale_date', 'cashier', 'notes')
    list_filter = ('payment_method', 'sale_date')
    search_fields = ('transaction_id', 'notes')
    readonly_fields = ('transaction_id', 'grand_total', 'sale_date')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('transaction_items')

@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'product', 'quantity_sold', 'total_amount')
    list_filter = ('transaction__payment_method',)
    search_fields = ('product__name',)
    readonly_fields = ('total_amount',)