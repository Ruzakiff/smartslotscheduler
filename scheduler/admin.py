from django.contrib import admin
from .models import Service, Booking

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'duration', 'price', 'active')
    list_filter = ('active', 'business', 'price')
    search_fields = ('name', 'business__name')
    list_editable = ('active', 'price')  # Quick edit in list view
    
    # Add inline bookings view
    class BookingInline(admin.TabularInline):
        model = Booking
        extra = 0
        
    inlines = [BookingInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('business', 'service', 'customer', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'business', 'start_time')
    search_fields = ('customer__name', 'customer__email', 'business__name')
    readonly_fields = ('created_at',)
    ordering = ('-start_time',)
    
    # Add fieldsets for better organization
    fieldsets = (
        ('Booking Info', {
            'fields': ('business', 'service', 'customer')
        }),
        ('Time Details', {
            'fields': ('start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
