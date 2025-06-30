from django.urls import path
from .views import OrderView

urlpatterns = [
  path('', OrderView.as_view(), name='order'),
  path('list/', OrderView.as_view(), name='order-list'),
]