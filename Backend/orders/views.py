from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer


class OrderView(generics.GenericAPIView, CreateModelMixin):
  queryset = Order.objects.all()
  serializer_class = OrderSerializer

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
