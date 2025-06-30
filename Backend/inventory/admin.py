from django.contrib import admin
from .models import Product, Category

# admin.site.register(Product)
# admin.site.register(Category)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
  list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
  list_display = ('name', 'price', 'description', 'quantity', 'category')
  list_filter = ('category',)
