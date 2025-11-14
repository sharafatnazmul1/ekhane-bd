from django import forms
from .models import Store


class StoreSettingsForm(forms.ModelForm):
    """Form for updating store settings"""

    class Meta:
        model = Store
        fields = ['store_name', 'status']
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter store name'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'store_name': 'Store Name',
            'status': 'Store Status',
        }
        help_texts = {
            'store_name': 'This is the name that will be displayed on your storefront',
            'status': 'Active stores are visible to customers, Draft stores are hidden',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make subdomain readonly by excluding 'expired' status if not already expired
        if self.instance and self.instance.status != 'expired':
            # Remove 'expired' from status choices
            self.fields['status'].choices = [
                choice for choice in self.fields['status'].choices
                if choice[0] != 'expired'
            ]
