from django.shortcuts import render
from .models import Product
from .serializers import ProductSerializer
from rest_framework import mixins, generics
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response


class ProductCreate(mixins.CreateModelMixin, generics.GenericAPIView):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_classes = [IsAdminUser] # Admin only create products

  def post(self, request, *args, **kwargs):
    return self.create(request, *args, **kwargs)


class ProductList(mixins.ListModelMixin, generics.GenericAPIView):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_classes = [AllowAny] # Listing is for everyone to view the list of products
  

  def get(self, request, *args, **kwargs):
    return self.list(request, *args, **kwargs)


class ProductDetails(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_classes = [IsAdminUser] # Updating and deleting products is only for admins

  def get(self, request, *args, **kwargs):
    return self.retrieve(request, *args, **kwargs)
  
  def put(self, request, *args, **kwargs):
    # ensure multipart/form-data is handles
    instance = self.get_object() # Retrieve the existing instance
    serializer = self.get_serializer(instance, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)
    return Response(serializer.data)
    # return self.update(request, *args, **kwargs)
  
  def delete(self, request, *args, **kwargs):
    return self.destroy(request, *args, **kwargs)
