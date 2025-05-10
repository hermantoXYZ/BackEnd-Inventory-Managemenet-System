from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from .models import Category, Product, Transaction, TransactionItem
from .serializers import (
    CategorySerializer, 
    ProductSerializer, 
    TransactionSerializer, 
    TransactionItemSerializer,
    TransactionCreateSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Category.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category', None)
        name = self.request.query_params.get('name', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        available = self.request.query_params.get('available', None)

        if category is not None:
            queryset = queryset.filter(category__slug=category)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if available is not None:
            queryset = queryset.filter(is_available=available.lower() == 'true')

        return queryset


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'status']
    search_fields = ['transaction_id', 'notes']
    ordering_fields = ['created_at', 'total_amount']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TransactionCreateSerializer
        return TransactionSerializer

    def get_queryset(self):
        queryset = Transaction.objects.all()
        transaction_type = self.request.query_params.get('transaction_type', None)
        status_param = self.request.query_params.get('status', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if transaction_type is not None:
            queryset = queryset.filter(transaction_type=transaction_type)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        if date_from is not None:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to is not None:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_param = request.query_params.get('status', None)
        if status_param:
            transactions = Transaction.objects.filter(status=status_param)
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "Status parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        transaction_type = request.query_params.get('type', None)
        if transaction_type:
            transactions = Transaction.objects.filter(transaction_type=transaction_type)
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "Type parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class TransactionItemViewSet(viewsets.ModelViewSet):
    queryset = TransactionItem.objects.all()
    serializer_class = TransactionItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction', 'product']

    def get_queryset(self):
        queryset = TransactionItem.objects.all()
        transaction_id = self.request.query_params.get('transaction_id', None)
        product_id = self.request.query_params.get('product_id', None)
        
        if transaction_id is not None:
            queryset = queryset.filter(transaction__transaction_id=transaction_id)
        if product_id is not None:
            queryset = queryset.filter(product__id=product_id)
            
        return queryset