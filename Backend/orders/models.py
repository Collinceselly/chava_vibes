from django.db import models
import uuid
from django.utils import timezone

def generate_transaction_id():
    return f"OON{uuid.uuid4().hex[:8].upper()}"

class Order(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    delivery_address = models.TextField(null=True)
    delivery_option = models.CharField(max_length=20, choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')])
    payment_method = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    additional_notes = models.TextField()
    cart_items = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    transactionId = models.CharField(max_length=50, unique=True, default=generate_transaction_id, editable=False)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('collected', 'Collected'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ])
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.id} by {self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['-created_at']