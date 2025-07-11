from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'transactionId', 'timestamp']

    def to_internal_value(self, data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Received data in to_internal_value: {data}")
        # Map camelCase to snake_case
        mapped_data = {
            'first_name': data.get('first_name') or data.get('firstName'),
            'last_name': data.get('last_name') or data.get('lastName'),
            'phone_number': data.get('phone_number') or data.get('phoneNumber'),
            'email_address': data.get('email_address') or data.get('emailAddress'),
            'delivery_address': data.get('delivery_address') or data.get('deliveryAddress'),
            'delivery_option': data.get('delivery_option') or data.get('deliveryOption'),
            'payment_method': data.get('payment_method') or data.get('paymentMethod'),
            'total': data.get('total'),
            'additional_notes': data.get('additional_notes') or data.get('additionalNotes'),
            'cart_items': data.get('cart_items') or data.get('cartItems', []),
            'status': data.get('status', 'pending'),
        }
        logger.info(f"Mapped data in to_internal_value: {mapped_data}")
        return super().to_internal_value(mapped_data)

    def validate(self, data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating data: {data}")
        if data.get('delivery_option') not in ['pickup', 'delivery']:
            raise serializers.ValidationError({'delivery_option': 'Must be "pickup" or "delivery"'})
        if data.get('status') not in [choice[0] for choice in Order._meta.get_field('status').choices]:
            raise serializers.ValidationError({'status': 'Invalid status value'})
        return data