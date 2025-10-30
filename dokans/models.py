from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.


class User(AbstractUser):
    phone = models.CharField(max_length=13, null=True, blank=True)
    username = models.EmailField(unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.usernamme
    

class Store(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Store')
    store_name = models.CharField(max_length=150)
    subdomain = models.CharField(max_length=50, unique=True)
    STATUS_CHOICES = (
        ("draft","Draft"),
        ("active","Active"),
        ("expired","Expired")
    )
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    trial_days = 7
    trial_end = models.DateField(default=timezone.now() + timedelta(days=trial_days))


    def is_trial_active(self):
        return timezone.now().date() <= self.trial_end
    
    def __str__(self):
        return f"{self.store_name} - {self.subdomain}.ekhane.bd"