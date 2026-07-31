from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    # Custom fields
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Address fields
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Morocco')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Shoe preferences
    shoe_size = models.CharField(max_length=10, blank=True)
    favorite_brands = models.CharField(max_length=200, blank=True)
    
    # Account status
    is_verified = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override fields from AbstractUser
    USERNAME_FIELD = 'email'  # Use email as username
    REQUIRED_FIELDS = ['username']  # Still need username for admin
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    @property
    def is_mahdi(self):
        return self.username == 'Mahdi@2005' or self.email == 'mahdi@2005.com'
