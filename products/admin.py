from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'parent', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'store', 'created_at')
    search_fields = ('name', 'description', 'store__store_name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('store', 'order', 'name')

    fieldsets = (
        ('Basic Information', {
            'fields': ('store', 'name', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category', 'price', 'sale_price', 'stock_quantity', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'store', 'category', 'created_at')
    search_fields = ('name', 'description', 'sku', 'store__store_name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    inlines = [ProductImageInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('store', 'category', 'name', 'slug', 'short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Inventory', {
            'fields': ('sku', 'stock_quantity', 'track_inventory', 'low_stock_threshold')
        }),
        ('Product Attributes', {
            'fields': ('weight', 'dimensions'),
            'classes': ('collapse',)
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('store', 'category')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')
    ordering = ('product', 'order', '-is_primary')

    fieldsets = (
        (None, {
            'fields': ('product', 'image', 'alt_text', 'is_primary', 'order')
        }),
    )
