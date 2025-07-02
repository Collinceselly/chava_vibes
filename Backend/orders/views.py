from django.shortcuts import render
from rest_framework import generics, status
from rest_framework import mixins, generics
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from rest_framework.permissions import AllowAny, IsAdminUser


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
    response = self.create(request, *args, **kwargs)
    if isinstance(response.data, dict) and 'id' in response.data:
      return Response({
        'status': 'success',
        'message': f'Order #{response.data["id"]} placed successfully'
      }, status=status.HTTP_201_CREATED)
    return Response({
      'status': 'error',
      'message': response.data
    }, status=status.HTTP_400_BAD_REQUEST)
  
  
