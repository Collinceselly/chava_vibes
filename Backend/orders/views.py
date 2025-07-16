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
from .notifications import send_sms  # Import the SMS function

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

        # Prepare order data with corrected keys and pass to serializer
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
            'cart_items': cart_items,  # Ensure cart_items is explicitly included
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

            # Send SMS notification after successful order creation
            order = serializer.instance
            phone_number = order.phone_number
            logger.info(f"Attempting to send SMS to: {phone_number}")
            message = f"Dear Customer,\nYour order No {order.transactionId} has been received and is being processed. Thank you for ordering with Chava Vibes Liquor Store."
            try:
                send_sms(phone_number, message)
                logger.info(f"SMS sent successfully to {phone_number}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")

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

class OrderDetails(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()  # Ensure instance is defined here
        old_status = instance.status  # Use the original status for comparison
        logger.info(f"Initial database state for order {instance.id}: status={instance.status}, delivery_option={instance.delivery_option}")
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Send SMS notification based on status and delivery option
        order = serializer.instance
        phone_number = order.phone_number
        logger.info(f"Updating order {order.id} with status: {order.status}, delivery_option: {order.delivery_option}, old status: {old_status}")

        try:
            # Debug conditions
            logger.info(f"Checking processing condition: order.status={order.status}, old_status={old_status}")
            if order.status == 'processing' and old_status == 'pending':
                message = f"Dear Customer,\nYour order No {order.transactionId} is being processed, we shall notify you as soon as it is ready. Thank you."
                logger.info(f"Sending SMS: {message}")
                send_sms(phone_number, message)
                logger.info(f"SMS sent for processing status to {phone_number}")
            elif order.status == 'ready_for_pickup' and old_status != 'ready_for_pickup' and order.delivery_option == 'pickup':
                message = f"Dear Customer,\nYour order No {order.transactionId} has been processed and ready for pick up. Visit our shop at Chava Vibes near Twin Kids Academy Umoja2. Thank you."
                logger.info(f"Sending SMS: {message}")
                send_sms(phone_number, message)
                logger.info(f"SMS sent for ready for pickup to {phone_number}")
            elif order.status == 'collected' and old_status != 'collected' and order.delivery_option == 'pickup':
                message = f"Dear Customer,\nYour order number {order.transactionId} has been collected. Thank you for ordering with Chava Vibes Liquor Store."
                logger.info(f"Sending SMS: {message}")
                send_sms(phone_number, message)
                logger.info(f"SMS sent for collected status to {phone_number}")
            elif order.status == 'shipped' and old_status != 'shipped' and order.delivery_option == 'delivery':
                message = f"Dear Customer,\nYour order No {order.transactionId} has been processed and issued and assigned for delivery. The rider shall contact you as soon as they arrive at your doorstep."
                logger.info(f"Sending SMS: {message}")
                send_sms(phone_number, message)
                logger.info(f"SMS sent for shipped status to {phone_number}")
            elif order.status == 'delivered' and old_status != 'delivered' and order.delivery_option == 'delivery':
                message = f"Dear Customer,\nYour order No {order.transactionId} has been successfully delivered, thank you for ordering with us and welcome again."
                logger.info(f"Sending SMS: {message}")
                send_sms(phone_number, message)
                logger.info(f"SMS sent for delivered status to {phone_number}")
            else:
                logger.warning(f"No SMS sent for order {order.id}: No matching status transition")
        except Exception as e:
            logger.error(f"Failed to send SMS for order {order.id} update: {str(e)}", exc_info=True)

        return Response({
            'status': 'success',
            'message': f'Order #{order.id} updated successfully',
            'transactionId': order.transactionId
        }, status=status.HTTP_200_OK)
        
        def put(self, request, *args, **kwargs):
            kwargs['partial'] = True
            return self.update(request, *args, **kwargs)