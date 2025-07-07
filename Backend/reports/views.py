# reports/views.py

from rest_framework import generics, mixins # Import generics and mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView

from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.db.models import Q
from django.utils import timezone
import datetime


# --- Import models from their respective apps ---
from otc_sales.models import Transaction, TransactionItem
from otc_sales.serializers import TransactionSerializer # We need the TransactionSerializer from otc_sales
from inventory.models import Product # Product model from inventory

# --- API View to List All Transactions ---
class TransactionListReportAPIView(mixins.ListModelMixin, generics.GenericAPIView):
    """
    API endpoint to list all transactions.
    Supports filtering by date range (start_date, end_date) and search by transaction_id.
    """
    queryset = Transaction.objects.all().order_by('-sale_date') # Order by most recent first
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser] # Ensure only authenticated users can access

    def get_queryset(self):
        # Start with the base queryset
        queryset = super().get_queryset()

        # Filtering by date range (optional query parameters)
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(sale_date__date__gte=start_date)
            except ValueError:
                # For simplicity, invalid dates will just be ignored in get_queryset
                # More robust validation could be done in a serializer or custom filter backend
                pass 
        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(sale_date__date__lte=end_date)
            except ValueError:
                pass

        # Search by transaction_id (optional query parameter)
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(transaction_id__icontains=search_query)

        return queryset

    def get(self, request, *args, **kwargs):
        # The ListModelMixin provides the .list() method
        return self.list(request, *args, **kwargs)

# --- Your existing report API Views (Sales Summaries, Product Performance, etc.) ---
# These should also be in this file below the TransactionListReportAPIView

class SalesSummaryReportAPIView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, format=None):
        today = timezone.localdate()
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        date_filter = {}
        if start_date_str:
            try: start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__gte'] = start_date
            except ValueError: return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if end_date_str:
            try: end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__lte'] = end_date
            except ValueError: return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        base_qs = Transaction.objects.filter(**date_filter)
        daily_summary_overall = base_qs.aggregate(total_sales=Sum('grand_total'), num_transactions=Count('id'))
        sales_by_day = base_qs.annotate(date=TruncDate('sale_date')).values('date').annotate(total_sales=Sum('grand_total'), num_transactions=Count('id')).order_by('date')
        sales_by_week = base_qs.annotate(week=TruncWeek('sale_date')).values('week').annotate(total_sales=Sum('grand_total'), num_transactions=Count('id')).order_by('week')
        sales_by_month = base_qs.annotate(month=TruncMonth('sale_date')).values('month').annotate(total_sales=Sum('grand_total'), num_transactions=Count('id')).order_by('month')
        sales_by_year = base_qs.annotate(year=TruncYear('sale_date')).values('year').annotate(total_sales=Sum('grand_total'), num_transactions=Count('id')).order_by('year')
        response_data = {'overall_summary': {'total_sales': daily_summary_overall['total_sales'], 'num_transactions': daily_summary_overall['num_transactions'], 'start_date': start_date_str if start_date_str else None, 'end_date': end_date_str if end_date_str else None,}, 'sales_by_day': list(sales_by_day), 'sales_by_week': list(sales_by_week), 'sales_by_month': list(sales_by_month), 'sales_by_year': list(sales_by_year),}
        return Response(response_data, status=status.HTTP_200_OK)

class ProductPerformanceReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        date_filter = {}
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                date_filter['transaction__sale_date__date__gte'] = start_date
            except ValueError:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                date_filter['transaction__sale_date__date__lte'] = end_date
            except ValueError:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        base_qs = TransactionItem.objects.filter(**date_filter)

        # Get all products without limiting to top 20 initially
        all_products = base_qs.values('product__id', 'product__name', 'transaction__sale_date').annotate(
            total_quantity_sold=Sum('quantity_sold'), total_revenue=Sum('total_amount')
        ).order_by('product__id', 'transaction__sale_date')

        # Group by product for best and slowest moving
        best_selling_products = sorted(all_products, key=lambda x: x['total_quantity_sold'] or 0, reverse=True)[:5]
        slowest_moving_products = sorted(all_products, key=lambda x: x['total_quantity_sold'] or 0)[:5]

        response_data = {
            'best_selling_products': best_selling_products,
            'slowest_moving_products': slowest_moving_products,
        }
        return Response(response_data, status=status.HTTP_200_OK)

# class CashierPerformanceReportAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request, format=None):
#         start_date_str = request.query_params.get('start_date')
#         end_date_str = request.query_params.get('end_date')
#         date_filter = {}
#         if start_date_str:
#             try: start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__gte'] = start_date
#             except ValueError: return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         if end_date_str:
#             try: end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__lte'] = end_date
#             except ValueError: return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         cashier_sales = Transaction.objects.filter(**date_filter).values('cashier__id', 'cashier__username', 'cashier__first_name', 'cashier__last_name').annotate(total_sales_generated=Sum('grand_total'), num_transactions_handled=Count('id')).order_by('-total_sales_generated')
#         return Response(list(cashier_sales), status=status.HTTP_200_OK)

# class PaymentMethodBreakdownReportAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request, format=None):
#         start_date_str = request.query_params.get('start_date')
#         end_date_str = request.query_params.get('end_date')
#         date_filter = {}
#         if start_date_str:
#             try: start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__gte'] = start_date
#             except ValueError: return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         if end_date_str:
#             try: end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date(); date_filter['sale_date__date__lte'] = end_date
#             except ValueError: return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         payment_breakdown = Transaction.objects.filter(**date_filter).values('payment_method').annotate(total_sales=Sum('grand_total'), num_transactions=Count('id')).order_by('-total_sales')
#         return Response(list(payment_breakdown), status=status.HTTP_200_OK)

# class ProfitabilityReportAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request, format=None):
#         start_date_str = request.query_params.get('start_date')
#         end_date_str = request.query_params.get('end_date')
#         date_filter = {}
#         if start_date_str:
#             try: start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date(); date_filter['transaction__sale_date__date__gte'] = start_date
#             except ValueError: return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         if end_date_str:
#             try: end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date(); date_filter['transaction__sale_date__date__lte'] = end_date
#             except ValueError: return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
#         profitable_items = TransactionItem.objects.filter(**date_filter).annotate(item_cost=ExpressionWrapper(F('quantity_sold') * F('product__cost_price'),output_field=DecimalField(max_digits=10, decimal_places=2)),gross_profit=ExpressionWrapper(F('total_amount') - (F('quantity_sold') * F('product__cost_price')),output_field=DecimalField(max_digits=10, decimal_places=2))).values('product__id', 'product__name', 'product__sku').annotate(total_revenue=Sum('total_amount'), total_cost_of_goods_sold=Sum('item_cost'), total_gross_profit=Sum('gross_profit'), total_quantity_sold=Sum('quantity_sold')).order_by('-total_gross_profit')
#         return Response(list(profitable_items), status=status.HTTP_200_OK)