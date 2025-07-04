# views.py

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework import status
import traceback

from .serializers import TransactionSerializer # Only need to import the main serializer

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_transaction(request):
    print('Raw Request Data:', request.data)
    print('Request User:', request.user)
    try:
        # Pass the entire request data directly to the TransactionSerializer
        # The TransactionSerializer's create method will handle nested transaction_items
        transaction_serializer = TransactionSerializer(data=request.data, context={'request': request})
        # This is where the validation process begins, potentially causing the error
        transaction_serializer.is_valid(raise_exception=True)
        transaction = transaction_serializer.save() # This calls the custom create in TransactionSerializer
        print('Transaction creation completed:', transaction)

        # Return the serialized data, which now includes the nested items due to to_representation
        return Response(transaction_serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        print('Exception occurred:', str(e))
        print('Stack trace:', traceback.format_exc())
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
  

