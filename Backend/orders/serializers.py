from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email_address', 
                  'delivery_address', 'delivery_option', 'payment_method', 'total', 
                  'cart_items', 'created_at']
        read_only_fields = ['id', 'created_at']

    def to_internal_value(self, data):
        # Map camelCase to snake_case
        mapped_data = {
            'first_name': data.get('firstName'),
            'last_name': data.get('lastName'),
            'phone_number': data.get('phoneNumber'),
            'email_address': data.get('emailAddress'),
            'delivery_address': data.get('deliveryAddress'),
            'delivery_option': data.get('deliveryOption'),
            'payment_method': data.get('paymentMethod'),
            'total': data.get('total'),  # Already snake_case, no mapping needed
            'cart_items': data.get('cartItems'),
        }
        return super().to_internal_value(mapped_data)

    def validate(self, data):
        # Add custom validation if needed (e.g., delivery_option choices)
        if data.get('delivery_option') not in ['pickup', 'delivery']:
            raise serializers.ValidationError({'delivery_option': 'Must be "pickup" or "delivery"'})
        return data