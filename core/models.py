from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Business(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    booking_url = models.SlugField(unique=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'business'        # Singular form
        verbose_name_plural = 'businesses'  # Plural form
        ordering = ['-created_at']       # Default ordering
    
    def save(self, *args, **kwargs):
        if not self.booking_url:
            self.booking_url = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name