from django.contrib import admin
from .models import Order

# admin.site.register(Order)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
  list_display = ['first_name', 'last_name', 'phone_number', 'email_address', 'delivery_address', 'delivery_option', 'payment_method']
