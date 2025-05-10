from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    transaction_id = models.CharField(max_length=50, unique=True, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate transaksi ID dengan format PREFIX-DATE-UUID
            prefix = {
                'purchase': 'PUR',
                'sale': 'SAL',
                'return': 'RET',
                'adjustment': 'ADJ'
            }.get(self.transaction_type, 'TRX')
            
            date_str = self.created_at.strftime('%Y%m%d') if self.created_at else timezone.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4()).split('-')[0].upper()
            self.transaction_id = f"{prefix}-{date_str}-{unique_id}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_transaction_type_display()}"

class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    def save(self, *args, **kwargs):
        # Hitung subtotal
        self.subtotal = self.quantity * self.unit_price
        
        # Simpan terlebih dahulu untuk mendapatkan ID jika baru
        super().save(*args, **kwargs)
        
        # Update stok produk
        product = self.product
        transaction_type = self.transaction.transaction_type
        
        # Jika ini adalah item baru atau kuantitas diubah
        if transaction_type == 'purchase':
            # Untuk pembelian, tambahkan ke stok
            product.stock += self.quantity
        elif transaction_type == 'sale':
            # Untuk penjualan, kurangi dari stok
            if product.stock >= self.quantity:
                product.stock -= self.quantity
            else:
                raise ValueError(f"Stok tidak cukup untuk produk {product.name}. Tersedia: {product.stock}")
        elif transaction_type == 'return':
            # Untuk pengembalian, tergantung dari jenis transaksi terkait
            # Di sini kita asumsikan pengembalian barang yang terjual (menambah stok)
            product.stock += self.quantity
        elif transaction_type == 'adjustment':
            # Untuk penyesuaian, kita bisa menambah atau mengurangi stok
            # Implementasi tergantung kebutuhan bisnis
            pass
        
        product.save()
    
    def delete(self, *args, **kwargs):
        # Sebelum menghapus item, kembalikan stok ke kondisi semula
        product = self.product
        transaction_type = self.transaction.transaction_type
        
        if transaction_type == 'purchase':
            # Batalkan penambahan stok
            product.stock -= self.quantity
        elif transaction_type == 'sale':
            # Batalkan pengurangan stok
            product.stock += self.quantity
        elif transaction_type == 'return':
            # Batalkan penambahan stok
            product.stock -= self.quantity
        
        product.save()
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.product.name} ({self.quantity})"
