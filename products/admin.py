from django.contrib import admin
from .models import Category, Product, Transaction, TransactionItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_available']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'transaction_type', 'status', 'total_amount', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at', 'updated_at']
    search_fields = ['transaction_id', 'notes']
    list_editable = ['status']
@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['transaction', 'product']
    search_fields = ['transaction__transaction_id', 'product__name']
    list_editable = ['quantity', 'unit_price']