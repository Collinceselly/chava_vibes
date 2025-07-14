from django.urls import path
from .views import OrderCreate, OrderList, OrderDetails

urlpatterns = [
  path('create/', OrderCreate.as_view(), name='order'),
  path('list/', OrderList.as_view(), name='order-list'),
  path('update/<int:pk>/', OrderDetails.as_view(), name='order-update')
]