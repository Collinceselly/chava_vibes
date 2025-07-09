from django.urls import path
from .views import create_transaction, my_otc_transactions


urlpatterns = [
  path('create/', create_transaction),
  path('my-transactions/', my_otc_transactions)
]