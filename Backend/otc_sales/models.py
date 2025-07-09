# models.py

from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product
import uuid
from django.conf import settings

def generate_transaction_id():
    return f"OTC{uuid.uuid4().hex[:8].upper()}"

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True, default=generate_transaction_id)
    payment_method = models.CharField(max_length=50, choices=[('cash', 'Cash'), ('card', 'Card'), ('mobile', 'Mobile Money')], default='cash')
    sale_date = models.DateTimeField(auto_now_add=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.transaction_id

    # --- REMOVE THIS BLOCK ---
    # def save(self, *args, **kwargs):
    #     if not self.grand_total:
    #         self.grand_total = sum(item.total_amount for item in self.transaction_items.all())
    #     super().save(*args, **kwargs)
    # --- END REMOVE BLOCK ---

    # Your Transaction model's save method should now just be:
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transaction_items')
    quantity_sold = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold}"

    def save(self, *args, **kwargs):
        # Keep this logic, as `self.product` will be a valid instance when this is called.
        if not self.total_amount:
            self.total_amount = self.quantity_sold * self.product.price
        super().save(*args, **kwargs)

        # Keep this logic as well, but ensure it's robust.
        # It's generally better to update product quantity *after* the transaction
        # and its items are fully committed, perhaps using signals or a custom management command,
        # to ensure atomicity. But for now, this can remain if it's not the cause of THIS specific error.
        self.product.quantity -= self.quantity_sold
        if self.product.quantity < 0:
            raise ValueError("Insufficient stock for transaction item")
        self.product.save()