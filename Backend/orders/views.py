from django.shortcuts import render
from rest_framework import generics, status
from rest_framework import mixins, generics
from rest_framework.response import Response
from .models import Order
from inventory.models import Product
from .serializers import OrderSerializer
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class OrderList(generics.GenericAPIView, mixins.ListModelMixin):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class OrderCreate(generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        logger.info(f"Received request data: {data}")

        # Extract and validate cart items for stock management
        cart_items = data.get('cartItems', [])
        if not cart_items:
            return Response({
                'status': 'error',
                'message': 'Cart is empty.'
            }, status=status.HTTP_400_BAD_REQUEST)

        for item in cart_items:
            try:
                product = Product.objects.get(id=item.get('id'))
                quantity = item.get('quantity', 0)
                if quantity <= 0 or product.quantity < quantity:
                    return Response({
                        'status': 'error',
                        'message': f'Insufficient stock for {product.name} or invalid quantity.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                product.quantity -= quantity
                product.save()
            except Product.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Product with ID {item.get("id")} not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'Error processing item: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare order data with corrected keys
        order_data = {
            'first_name': data.get('firstName'),
            'last_name': data.get('lastName'),
            'phone_number': data.get('phoneNumber'),
            'email_address': data.get('emailAddress'),
            'delivery_address': data.get('deliveryAddress'),
            'delivery_option': data.get('deliveryOption'),
            'payment_method': data.get('paymentMethod'),
            'total': data.get('total'),
            'additional_notes': data.get('additionalNotes'),
            'cart_items': data.get('cartItems'),
            'status': data.get('status', 'pending'),
        }
        logger.info(f"Prepared order data: {order_data}")

        try:
            serializer = self.get_serializer(data=order_data)
            logger.info(f"Serializer initial data: {serializer.initial_data}")
            serializer.is_valid(raise_exception=True)
            logger.info(f"Validated data: {serializer.validated_data}")
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({
                'status': 'success',
                'message': f'Order #{serializer.instance.id} placed successfully',
                'transactionId': serializer.instance.transactionId
            }, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)