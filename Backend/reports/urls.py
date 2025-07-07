from django.urls import path
from .views import TransactionListReportAPIView, SalesSummaryReportAPIView, ProductPerformanceReportAPIView


urlpatterns = [
  path('', TransactionListReportAPIView.as_view()),
  path('sales-summary/', SalesSummaryReportAPIView.as_view()),
  path('product-performance/', ProductPerformanceReportAPIView.as_view())
]