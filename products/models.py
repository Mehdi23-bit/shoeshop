from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/')
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Shoe(models.Model):
    GENDER_CHOICES = [
        ('M', 'Men'),
        ('W', 'Women'),
        ('K', 'Kids'),
        ('U', 'Unisex'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='shoes',null=True)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    sizes = models.JSONField(default=list)  # ['7', '8', '9', '10']
    colors = models.JSONField(default=list)
    description = models.TextField()
    materials = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='shoes/',null=True)
    def __str__(self):
        return self.name
    
    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price

class ShoeImage(models.Model):
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shoes/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=100, blank=True)




class Order(models.Model):
    """
    Order model for tracking customer purchases
    """
    
    # Order Status Choices
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Status Choices
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Method Choices
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('stripe', 'Stripe'),
    ]
    
    # Shipping Method Choices
    SHIPPING_METHOD_CHOICES = [
        ('standard', 'Standard Shipping (3-5 days)'),
        ('express', 'Express Shipping (1-2 days)'),
        ('overnight', 'Overnight Shipping'),
        ('pickup', 'Store Pickup'),
    ]
    
    # ===== Basic Information =====
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders'
    )
    
    # ===== Customer Information =====
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # ===== Shipping Information =====
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100, default='Morocco')
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_method = models.CharField(
        max_length=20, 
        choices=SHIPPING_METHOD_CHOICES, 
        default='standard'
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    
    # ===== Billing Information =====
    billing_address = models.TextField(blank=True)
    same_as_shipping = models.BooleanField(default=True)
    
    # ===== Order Items =====
    items = models.JSONField(default=dict)  # Stores cart items with details
    item_count = models.IntegerField(default=0)
    
    # ===== Pricing =====
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # ===== Payment Information =====
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='cash'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # ===== Order Status =====
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # ===== Timestamps =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # ===== Customer IP and Session =====
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not set
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number: ORD-2024-0001"""
        today = timezone.now()
        year = today.strftime('%Y')
        month = today.strftime('%m')
        
        # Get last order number for this month
        prefix = f"ORD-{year}{month}"
        last_order = Order.objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        
        if last_order:
            # Extract the number and increment
            last_num = int(last_order.order_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def calculate_totals(self):
        """Calculate subtotal, tax, discount, and total"""
        self.subtotal = Decimal('0.00')
        
        # Calculate from items
        for item_data in self.items.values():
            price = Decimal(str(item_data.get('price', 0)))
            quantity = item_data.get('quantity', 1)
            self.subtotal += price * quantity
        
        # Calculate tax (10%)
        self.tax = self.subtotal * Decimal('0.10')
        
        # Apply discount if any
        if self.discount:
            self.total = self.subtotal + self.tax - self.discount + self.shipping_cost
        else:
            self.total = self.subtotal + self.tax + self.shipping_cost
        
        # Count items
        self.item_count = sum(item.get('quantity', 0) for item in self.items.values())
        
        return self.total
    
    def mark_as_paid(self):
        """Mark order as paid"""
        self.payment_status = 'paid'
        self.paid_at = timezone.now()
        self.status = 'confirmed'
        self.save()
    
    def mark_as_shipped(self, tracking_number=None):
        """Mark order as shipped"""
        self.status = 'shipped'
        if tracking_number:
            self.tracking_number = tracking_number
        self.save()
    
    def mark_as_delivered(self):
        """Mark order as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def cancel_order(self):
        """Cancel order and restore stock"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
        
        # Restore stock for all items
        from .models import Shoe
        for item_id, item_data in self.items.items():
            try:
                shoe = Shoe.objects.get(id=int(item_id))
                shoe.stock += item_data.get('quantity', 0)
                shoe.save()
            except Shoe.DoesNotExist:
                pass
    
    def get_total_items(self):
        """Get total number of items in order"""
        return sum(item.get('quantity', 0) for item in self.items.values())
    
    def get_items_list(self):
        """Get formatted list of items"""
        items_list = []
        from .models import Shoe
        
        for item_id, item_data in self.items.items():
            try:
                shoe = Shoe.objects.get(id=int(item_id))
                items_list.append({
                    'id': item_id,
                    'name': shoe.name,
                    'price': item_data.get('price', shoe.price),
                    'quantity': item_data.get('quantity', 1),
                    'size': item_data.get('size', 'N/A'),
                    'subtotal': Decimal(str(item_data.get('price', shoe.price))) * item_data.get('quantity', 1),
                    'image': shoe.image.url if shoe.image else None,
                })
            except Shoe.DoesNotExist:
                items_list.append({
                    'id': item_id,
                    'name': 'Product Unavailable',
                    'price': item_data.get('price', 0),
                    'quantity': item_data.get('quantity', 1),
                    'size': item_data.get('size', 'N/A'),
                    'subtotal': Decimal(str(item_data.get('price', 0))) * item_data.get('quantity', 1),
                    'image': None,
                })
        
        return items_list
    
    @property
    def status_badge_color(self):
        """Get Bootstrap badge color for status"""
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'info',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def payment_status_badge_color(self):
        """Get Bootstrap badge color for payment status"""
        colors = {
            'pending': 'warning',
            'paid': 'success',
            'failed': 'danger',
            'refunded': 'secondary',
        }
        return colors.get(self.payment_status, 'secondary')
    
    @property
    def is_completed(self):
        """Check if order is completed"""
        return self.status in ['delivered', 'cancelled', 'refunded']
    
    @property
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed', 'processing']
    
    @property
    def days_since_created(self):
        """Get days since order was created"""
        delta = timezone.now() - self.created_at
        return delta.days


class OrderItem(models.Model):
    """
    Individual order items (alternative to JSON field)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    shoe = models.ForeignKey('Shoe', on_delete=models.SET_NULL, null=True)
    shoe_name = models.CharField(max_length=200)
    shoe_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    size = models.CharField(max_length=20, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.shoe_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.shoe_price * self.quantity
        super().save(*args, **kwargs)    
