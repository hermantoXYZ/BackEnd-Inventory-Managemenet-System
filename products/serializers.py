from rest_framework import serializers
from .models import Category, Product, Transaction, TransactionItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'name', 'slug', 'description',
            'price', 'stock', 'is_available', 'image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

class ProductSimpleSerializer(serializers.ModelSerializer):
    """A simplified serializer for Product to use in nested relationships"""
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock']


class TransactionItemSerializer(serializers.ModelSerializer):
    product_details = ProductSimpleSerializer(source='product', read_only=True)
    
    class Meta:
        model = TransactionItem
        fields = ['id', 'transaction', 'product', 'product_details', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['subtotal']


class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True, read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'transaction_type_display', 
            'status', 'status_display', 'total_amount', 'notes', 'created_at', 
            'updated_at', 'items'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'updated_at']


class TransactionItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionItem
        fields = ['product', 'quantity', 'unit_price']


class TransactionCreateSerializer(serializers.ModelSerializer):
    items = TransactionItemCreateSerializer(many=True)
    
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'status', 'total_amount', 'notes', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        transaction = Transaction.objects.create(**validated_data)
        
        for item_data in items_data:
            TransactionItem.objects.create(transaction=transaction, **item_data)
        
        return transaction
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update transaction fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If items are provided, handle them
        if items_data is not None:
            # First, remove existing items
            instance.items.all().delete()
            
            # Then create new items
            for item_data in items_data:
                TransactionItem.objects.create(transaction=instance, **item_data)
        
        return instance