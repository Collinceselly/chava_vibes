from rest_framework import serializers
from .models import Order
import re

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'transactionId', 'timestamp']

    def to_internal_value(self, data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Received data in to_internal_value: {data}")
        # Map provided fields, ensuring cart_items is always included for creation
        mapped_data = {}
        if 'status' in data:
            mapped_data['status'] = data.get('status', 'pending')
        if 'first_name' in data or 'firstName' in data:
            mapped_data['first_name'] = data.get('first_name') or data.get('firstName')
        if 'last_name' in data or 'lastName' in data:
            mapped_data['last_name'] = data.get('last_name') or data.get('lastName')
        if 'phone_number' in data or 'phoneNumber' in data:
            phone_number = data.get('phone_number') or data.get('phoneNumber')
            # Normalize phone number to ensure correct +254 format
            if phone_number:
                # Remove any existing country code (+254 or 0) and extra characters
                phone_number = re.sub(r'^\+?2540?|^0', '', phone_number)  # Remove +254, +2540, or leading 0
                phone_number = phone_number.strip()  # Remove any whitespace
                if len(phone_number) == 9:  # Assume 9 digits is the local number
                    phone_number = f"+254{phone_number}"
                else:
                    raise serializers.ValidationError({'phone_number': 'Invalid phone number length; must be 9 digits after country code'})
                phone_number = phone_number[:13]  # Limit to +254 followed by 9 digits
            mapped_data['phone_number'] = phone_number
        if 'email_address' in data or 'emailAddress' in data:
            mapped_data['email_address'] = data.get('email_address') or data.get('emailAddress')
        if 'delivery_address' in data or 'deliveryAddress' in data:
            mapped_data['delivery_address'] = data.get('delivery_address') or data.get('deliveryAddress')
        if 'delivery_option' in data or 'deliveryOption' in data:
            mapped_data['delivery_option'] = data.get('delivery_option') or data.get('deliveryOption')
        if 'payment_method' in data or 'paymentMethod' in data:
            mapped_data['payment_method'] = data.get('payment_method') or data.get('paymentMethod')
        if 'total' in data:
            mapped_data['total'] = data.get('total')
        if 'additional_notes' in data or 'additionalNotes' in data:
            mapped_data['additional_notes'] = data.get('additional_notes') or data.get('additionalNotes')
        # Ensure cart_items is always included, defaulting to empty list if not provided
        mapped_data['cart_items'] = data.get('cart_items') or data.get('cartItems', [])
        logger.info(f"Mapped data in to_internal_value: {mapped_data}")
        return super().to_internal_value(mapped_data)

    def validate(self, data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating data: {data}")
        # Only validate fields that are provided
        if 'delivery_option' in data and data.get('delivery_option') not in ['pickup', 'delivery']:
            raise serializers.ValidationError({'delivery_option': 'Must be "pickup" or "delivery"'})
        if 'status' in data and data.get('status') not in [choice[0] for choice in Order._meta.get_field('status').choices]:
            raise serializers.ValidationError({'status': 'Invalid status value'})
        # Ensure cart_items is a list if provided
        if 'cart_items' in data and not isinstance(data.get('cart_items'), list):
            raise serializers.ValidationError({'cart_items': 'Must be a list'})
        # Conditional validation for delivery_address
        if 'delivery_option' in data and data.get('delivery_option') == 'delivery':
            if 'delivery_address' not in data or not data.get('delivery_address'):
                raise serializers.ValidationError({'delivery_address': 'Delivery address is required for delivery orders'})
        # Validate phone number format
        if 'phone_number' in data:
            phone_number = data.get('phone_number')
            logger.info(f"Validating phone number: {phone_number}")
            if not phone_number or not re.match(r'^\+254\d{9}$', phone_number):
                raise serializers.ValidationError({'phone_number': 'Phone number must be in +254XXXXXXXXX format (10 digits after +254)'})
        return data

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Updating instance with validated_data: {validated_data}")
        # Update only the fields that are provided
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance