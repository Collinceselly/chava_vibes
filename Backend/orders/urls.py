from django.urls import path
from .views import OrderCreate, OrderList

urlpatterns = [
  path('create/', OrderCreate.as_view(), name='order'),
  path('list/', OrderList.as_view(), name='order-list'),
]