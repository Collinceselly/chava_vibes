from django.urls import path
# from rest_framework.routers import DefaultRouter
from . import views

# router = DefaultRouter()
# router.register(r'products', ProductList)

urlpatterns = [
  path('products/', views.ProductList.as_view()),
  path('product/<int:pk>', views.ProductList.as_view())
]