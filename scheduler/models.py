from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from core.models import Customer, Business

class Service(models.Model):
    business = models.ForeignKey('core.Business', on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business.name} - {self.name}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    business = models.ForeignKey('core.Business', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    customer = models.ForeignKey('core.Customer', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['business', 'start_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.service.name} - {self.start_time}"

# Create your models here.
