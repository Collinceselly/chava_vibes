from django.shortcuts import render
from .models import Product
from .serializers import ProductSerializer
from rest_framework import mixins, generics

class ProductList(mixins.ListModelMixin, mixins.RetrieveModelMixin, generics.GenericAPIView):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_class = []

  def get(self, request, *args, **kwargs):
    if 'pk' in kwargs:
      return self.retrieve(request, *args, **kwargs)
    return self.list(request, *args, **kwargs)
