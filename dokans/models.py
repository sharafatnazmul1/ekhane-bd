from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.


def get_default_trial_end():
    """Returns default trial end date (7 days from now)"""
    return timezone.now().date() + timedelta(days=7)


class User(AbstractUser):
    phone = models.CharField(max_length=13, null=True, blank=True)
    username = models.EmailField(unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username


class Store(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store')
    store_name = models.CharField(max_length=150, help_text="The name of your store")
    subdomain = models.CharField(max_length=50, unique=True, help_text="Unique subdomain for your store (e.g., 'myshop' for myshop.ekhane.bd)")
    STATUS_CHOICES = (
        ("draft","Draft"),
        ("active","Active"),
        ("expired","Expired")
    )
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    trial_days = 7
    trial_end = models.DateField(default=get_default_trial_end)
    
    def is_trial_active(self):
        return timezone.now().date() <= self.trial_end
    
    def __str__(self):
        return f"{self.store_name} - {self.subdomain}.ekhane.bd"