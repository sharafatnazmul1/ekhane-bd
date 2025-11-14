from django.contrib import admin
from .models import Customer, Cart, CartItem, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'price', 'quantity', 'total')
    can_delete = False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'store', 'total_orders', 'total_spent', 'created_at')
    list_filter = ('store', 'created_at')
    search_fields = ('name', 'email', 'phone', 'store__store_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Customer Information', {
            'fields': ('store', 'name', 'email', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'customer', 'total_items', 'subtotal', 'created_at', 'updated_at')
    list_filter = ('store', 'created_at')
    search_fields = ('customer__name', 'customer__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'price', 'total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'cart__customer__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'store', 'customer', 'status', 'payment_method', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'store', 'created_at')
    search_fields = ('order_number', 'customer__name', 'customer__email', 'shipping_phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)

    fieldsets = (
        ('Order Information', {
            'fields': ('store', 'order_number', 'customer', 'status')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'subtotal', 'shipping_cost', 'total')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_email', 'shipping_phone',
                      'shipping_address', 'shipping_division', 'shipping_district', 'shipping_area')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'price', 'total')
    list_filter = ('order__created_at',)
    search_fields = ('product_name', 'product_sku', 'order__order_number')
    readonly_fields = ('total',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'status', 'transaction_id', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__order_number', 'transaction_id', 'bkash_payment_id', 'bkash_trx_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'amount', 'status', 'transaction_id')
        }),
        ('bKash Details', {
            'fields': ('bkash_payment_id', 'bkash_trx_id', 'bkash_transaction_status'),
            'classes': ('collapse',)
        }),
        ('Debug Information', {
            'fields': ('raw_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
