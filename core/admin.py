from django.contrib import admin
from .models import Business, Customer

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'booking_url', 'email', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'booking_url', 'email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    # Add inline services view
    class ServiceInline(admin.TabularInline):
        from scheduler.models import Service
        model = Service
        extra = 1

    inlines = [ServiceInline]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    # Add inline bookings view
    class BookingInline(admin.TabularInline):
        from scheduler.models import Booking
        model = Booking
        extra = 0

    inlines = [BookingInline]
