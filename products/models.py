from django.db import models
from django.utils.text import slugify
from dokans.models import Store


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        unique_together = ['store', 'slug']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.store.store_name})"


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leave empty if no sale")

    # Inventory
    sku = models.CharField(max_length=100, blank=True, help_text="Stock Keeping Unit")
    stock_quantity = models.IntegerField(default=0)
    track_inventory = models.BooleanField(default=True)
    low_stock_threshold = models.IntegerField(default=5, help_text="Alert when stock is below this number")

    # Product attributes
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H in cm")

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['store', 'slug']
        indexes = [
            models.Index(fields=['store', 'is_active']),
            models.Index(fields=['store', 'category']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            # Auto-generate SKU
            self.sku = f"SKU-{self.store.id}-{slugify(self.name)[:20]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.store.store_name}"

    @property
    def final_price(self):
        """Return sale price if available, otherwise regular price"""
        if self.sale_price and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.sale_price and self.sale_price < self.price:
            return int(((self.price - self.sale_price) / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if stock is below threshold"""
        if not self.track_inventory:
            return False
        return 0 < self.stock_quantity <= self.low_stock_threshold

    def get_primary_image(self):
        """Get the primary product image"""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_primary', '-created_at']

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

        # If this is the first image, make it primary
        if self.product.images.count() == 1:
            self.is_primary = True
            super().save(update_fields=['is_primary'])

    def __str__(self):
        return f"Image for {self.product.name}"
