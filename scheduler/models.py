from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from core.models import Customer, Business
from django.core.exceptions import ValidationError
from django.utils import timezone

class Service(models.Model):
    business = models.ForeignKey(Business, related_name='services', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} - {self.name}"

    class Meta:
        indexes = [
            models.Index(fields=['business', 'active']),
        ]
        ordering = ['name']

class BusinessHours(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    business = models.ForeignKey(Business, related_name='hours', on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['business', 'day_of_week']
        indexes = [
            models.Index(fields=['business', 'day_of_week']),
        ]
        ordering = ['day_of_week']

    def clean(self):
        if not self.is_closed and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

    def __str__(self):
        return f"{self.business.name} - {self.get_day_of_week_display()}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    business = models.ForeignKey(Business, related_name='bookings', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, related_name='bookings', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='bookings', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['business', 'start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")
        
        # Check for overlapping bookings
        overlapping = Booking.objects.filter(
            business=self.business,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=['pending', 'confirmed']
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            raise ValidationError("This time slot overlaps with another booking")

    def save(self, *args, **kwargs):
        if not self.end_time and self.start_time and self.service:
            # Auto-calculate end time based on service duration
            self.end_time = self.start_time + timezone.timedelta(minutes=self.service.duration)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.business.name} - {self.service.name} - {self.start_time}"

# Create your models here.
