from django import forms
from .models import Product, Category, ProductImage


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category description'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)

        if store:
            # Filter parent categories to only show categories from same store
            self.fields['parent'].queryset = Category.objects.filter(store=store)

        # Make parent optional
        self.fields['parent'].required = False


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'short_description', 'description',
            'price', 'sale_price', 'sku', 'stock_quantity',
            'track_inventory', 'low_stock_threshold',
            'weight', 'dimensions', 'is_active', 'is_featured',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description (max 500 chars)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Full product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty if no sale', 'step': '0.01'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty for auto-generation'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'track_inventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg', 'step': '0.01'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x W x H in cm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO title (optional)'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'SEO description (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)

        if store:
            # Filter categories to only show categories from same store
            self.fields['category'].queryset = Category.objects.filter(store=store, is_active=True)

        # Make some fields optional
        self.fields['sale_price'].required = False
        self.fields['sku'].required = False
        self.fields['weight'].required = False
        self.fields['dimensions'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['category'].required = False

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        sale_price = cleaned_data.get('sale_price')

        if sale_price and price and sale_price >= price:
            raise forms.ValidationError('Sale price must be less than regular price')

        return cleaned_data


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image description'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['alt_text'].required = False
