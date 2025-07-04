# serializers.py

from rest_framework import serializers
from .models import Transaction, TransactionItem
from inventory.models import Product
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from collections import defaultdict

# --- SimpleProductSerializer (No Change) ---
class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']

# --- TransactionItemSerializer (No Change from previous version - stock check removed) ---
class TransactionItemSerializer(serializers.ModelSerializer):
    product_input = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )
    product = SimpleProductSerializer(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = TransactionItem
        fields = [
            'id', 'product_input', 'product', 'quantity_sold', 'total_amount'
        ]
        read_only_fields = ['total_amount']

    def validate(self, data):
        product_instance = data.get('product')
        quantity_sold = data.get('quantity_sold')

        if quantity_sold is None or quantity_sold <= 0:
            raise serializers.ValidationError({"quantity_sold": "Quantity sold must be a positive number."})
        if product_instance is None:
            raise serializers.ValidationError({"product_input": "Product ID is required and must be valid."})

        data['total_amount'] = quantity_sold * product_instance.price
        return data

    def create(self, validated_data):
        # This method creates the TransactionItem instance.
        # Stock deduction is handled by the parent TransactionSerializer.
        transaction_instance = self.context.get('transaction')

        if transaction_instance is None or not hasattr(transaction_instance, 'pk') or not transaction_instance.pk:
            raise serializers.ValidationError("Internal Error: Transaction instance is missing or has no primary key.")

        validated_data['transaction'] = transaction_instance
        return TransactionItem.objects.create(**validated_data)


# --- TransactionSerializer (KEY CHANGES IN create method for concurrency) ---
class TransactionSerializer(serializers.ModelSerializer):
    cashier = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # A sale must have items, so required=True
    transaction_items = TransactionItemSerializer(many=True, required=True, write_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_id', 'payment_method', 'sale_date', 'grand_total', 'cashier', 'notes', 'transaction_items']
        read_only_fields = ['transaction_id', 'sale_date', 'grand_total']

    def validate(self, data):
        # super().validate(data) # Uncomment if you have specific model-level validations on Transaction

        transaction_items_data = data.get('transaction_items', [])

        if not transaction_items_data:
            raise serializers.ValidationError({"transaction_items": "At least one item is required for a sale."})

        # Dictionary to store the cumulative quantity sold for each product within this specific transaction
        cumulative_quantities = defaultdict(int)

        product_ids_in_request = set()
        for item_data in transaction_items_data:
            product_instance = item_data.get('product')
            if product_instance:
                product_ids_in_request.add(product_instance.id)
            else:
                raise serializers.ValidationError({"transaction_items": "One or more product IDs are invalid or missing."})

        # Fetch all required product instances for an early stock check.
        # Note: This is NOT yet locked, so its quantity can become stale.
        # The authoritative check will happen on locked instances in create().
        available_products_for_early_check = {
            p.id: p for p in Product.objects.filter(id__in=product_ids_in_request)
        }

        errors = defaultdict(list)
        total_grand_total = 0

        for index, item_data in enumerate(transaction_items_data):
            product_instance_from_item = item_data.get('product')
            quantity_sold = item_data.get('quantity_sold')

            if product_instance_from_item is None:
                errors[f'transaction_items[{index}]'].append("Product data is missing or invalid for this item.")
                continue
            if quantity_sold is None or quantity_sold <= 0:
                errors[f'transaction_items[{index}]'].append("Quantity sold must be a positive number for this item.")
                continue

            product_id = product_instance_from_item.id
            actual_product_instance = available_products_for_early_check.get(product_id)
            if not actual_product_instance:
                errors[f'transaction_items[{index}]'].append(f"Internal validation error: Product {product_id} not found for stock check.")
                continue

            cumulative_quantities[product_id] += quantity_sold

            # --- Early Cumulative Stock Check (not race-condition proof, but good initial filter) ---
            if cumulative_quantities[product_id] > actual_product_instance.quantity:
                errors[f'transaction_items[{index}]'].append(
                    f"Initial check: Insufficient stock for {actual_product_instance.name}. "
                    f"Available: {actual_product_instance.quantity}, "
                    f"Requested (cumulative in this request): {cumulative_quantities[product_id]}."
                )
            
            # Calculate total amount for this item and add to grand total
            item_total = quantity_sold * actual_product_instance.price
            item_data['total_amount'] = item_total # Store for consistency if needed
            total_grand_total += item_total

        if errors:
            raise serializers.ValidationError(errors)

        # Set grand_total here so it's available for the create method
        data['grand_total'] = total_grand_total
        return data

    def create(self, validated_data):
        # The entire sale creation process (including stock deduction) occurs within an atomic transaction.
        with transaction.atomic():
            transaction_items_data = validated_data.pop('transaction_items', [])
            
            # 1. Identify all unique product IDs involved in this transaction
            product_ids_to_lock = [item_data['product'].id for item_data in transaction_items_data]

            # 2. Lock the product rows needed for this transaction.
            # This is critical for preventing race conditions in a multi-user environment.
            # `select_for_update()` holds a lock until the transaction commits or rolls back.
            locked_products = Product.objects.filter(id__in=product_ids_to_lock).select_for_update()

            # Create a dictionary for efficient lookup of products by ID from the locked set
            locked_product_map = {product.id: product for product in locked_products}

            # To track cumulative quantity for the authoritative check
            cumulative_quantities_locked = defaultdict(int)
            products_to_save = [] # Collect product instances whose quantities will be updated

            # 3. Perform the authoritative stock deduction and final validation with locked products
            for index, item_data in enumerate(transaction_items_data):
                product_id = item_data['product'].id
                quantity_sold = item_data['quantity_sold']
                
                # Get the product instance from the *locked* set
                product = locked_product_map.get(product_id)

                if not product:
                    # This should ideally not happen if initial product_input validation is strong,
                    # but it's a safeguard if a product was deleted concurrently.
                    raise serializers.ValidationError({
                        f"transaction_items[{index}]": "Product not found or unavailable."
                    })
                
                # Accumulate quantity for this product across all items in the current transaction
                cumulative_quantities_locked[product_id] += quantity_sold

                # IMPORTANT: Perform the stock check on the *locked* product instance's current quantity.
                # This is the definitive check that prevents over-selling.
                if cumulative_quantities_locked[product_id] > product.quantity:
                    raise serializers.ValidationError({
                        f"transaction_items[{index}]": 
                        f"Insufficient stock for {product.name}. Available: {product.quantity}, "
                        f"Requested (cumulative in this sale): {cumulative_quantities_locked[product_id]}."
                    })
                
                # Apply the quantity deduction using F() expression.
                # The actual database write for this specific product happens when .save() is called.
                # Note: We're updating the 'product' object from `locked_product_map` directly.
                product.quantity = F('quantity') - quantity_sold
                products_to_save.append(product) # Add to list to save all modified products at once

            # 4. Save all deducted products *within the atomic block*. This applies the F() expressions.
            if products_to_save:
                for product in products_to_save:
                    product.save(update_fields=['quantity'])

            # Ensure cashier is set correctly.
            # CurrentUserDefault should usually handle this, but adding a fallback/check.
            cashier = validated_data.get('cashier')
            if not isinstance(cashier, User) and 'request' in self.context:
                validated_data['cashier'] = self.context['request'].user
            elif not isinstance(cashier, User):
                # If serializer is instantiated without request context and no user is provided.
                raise serializers.ValidationError({"cashier": "Cashier user could not be determined."})

            # 5. Create the main Transaction instance. grand_total is already in validated_data.
            sale = super().create(validated_data)

            # 6. Create TransactionItem instances, linking them to the newly created sale.
            # We iterate through the original transaction_items_data to get product details and quantities.
            for item_data in transaction_items_data:
                # The nested serializer's create method needs the 'transaction' instance in its context
                # and also the 'request' for any further context it might need.
                TransactionItemSerializer(
                    context={'request': self.context.get('request'), 'transaction': sale}
                ).create(item_data)

            return sale

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # CORRECTED: Access related TransactionItem objects using the name of the ManyToMany field
        # or the related_name defined on the ForeignKey in TransactionItem model.
        # The error message indicated 'transaction_items' is the correct attribute.
        ret['transaction_items'] = TransactionItemSerializer(instance.transaction_items.all(), many=True).data
        return ret