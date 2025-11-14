from django.db import models
from django.utils import timezone
from dokans.models import Store
from products.models import Product
import uuid


class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['store', 'email']
        indexes = [
            models.Index(fields=['store', 'email']),
            models.Index(fields=['store', 'phone']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.store.store_name}"

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def total_spent(self):
        from django.db.models import Sum
        total = self.orders.filter(payment_status='paid').aggregate(Sum('total'))['total__sum']
        return total or 0


class Cart(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='carts')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['store', 'session_key']),
            models.Index(fields=['store', 'customer']),
        ]

    def __str__(self):
        if self.customer:
            return f"Cart for {self.customer.name}"
        return f"Cart {self.session_key}"

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def add_item(self, product, quantity=1):
        """Add or update item in cart"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity, 'price': product.final_price}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item

    def remove_item(self, product):
        """Remove item from cart"""
        CartItem.objects.filter(cart=self, product=product).delete()

    def update_item_quantity(self, product, quantity):
        """Update item quantity"""
        if quantity <= 0:
            self.remove_item(product)
        else:
            CartItem.objects.filter(cart=self, product=product).update(quantity=quantity)

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of adding
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total(self):
        return self.quantity * self.price


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    # Order status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Shipping information
    shipping_name = models.CharField(max_length=200)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_division = models.CharField(max_length=100)
    shipping_district = models.CharField(max_length=100)
    shipping_area = models.CharField(max_length=100, blank=True)

    # Additional info
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['store', 'payment_status']),
            models.Index(fields=['order_number']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_id = str(uuid.uuid4().hex)[:6].upper()
        return f"ORD-{timestamp}-{random_id}"

    def __str__(self):
        return f"{self.order_number} - {self.customer.name if self.customer else 'Guest'}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=300)  # Store name in case product is deleted
    product_sku = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calculate total
        self.total = self.quantity * self.price

        # Store product info
        if self.product:
            self.product_name = self.product.name
            self.product_sku = self.product.sku

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} - Order {self.order.order_number}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # bKash specific fields
    bkash_payment_id = models.CharField(max_length=100, blank=True)
    bkash_trx_id = models.CharField(max_length=100, blank=True)
    bkash_transaction_status = models.CharField(max_length=50, blank=True)

    # Generic transaction ID (for future payment gateways)
    transaction_id = models.CharField(max_length=100, blank=True)

    # Response data (for debugging)
    raw_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for {self.order.order_number} - {self.payment_method}"

    def mark_as_completed(self, transaction_id=''):
        """Mark payment as completed"""
        self.status = 'completed'
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

        # Update order payment status
        self.order.payment_status = 'paid'
        self.order.save()

    def mark_as_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()

        # Update order payment status
        self.order.payment_status = 'failed'
        self.order.save()
