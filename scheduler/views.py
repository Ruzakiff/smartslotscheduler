from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from core.models import Business, Customer
from .models import Service, Booking, BusinessHours
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pytz

# Create your views here.

def booking_page(request, booking_url):
    """Public booking page for customers"""
    business = get_object_or_404(Business, booking_url=booking_url)
    services = Service.objects.filter(business=business, active=True)
    
    return render(request, 'scheduler/booking_page.html', {
        'business': business,
        'services': services,
    })

def get_available_slots(request, business_id):
    """API endpoint to get available time slots"""
    business = get_object_or_404(Business, id=business_id)
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')
    
    if not service_id:
        return JsonResponse({'error': 'Service ID is required'}, status=400)
    
    try:
        service = Service.objects.get(id=service_id, business=business)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get business hours for the day
        day_of_week = date.weekday()
        try:
            hours = BusinessHours.objects.get(
                business=business,
                day_of_week=day_of_week,
                is_closed=False
            )
            
            # Generate time slots with timezone awareness
            slots = []
            tz = pytz.timezone(timezone.get_current_timezone_name())
            current_time = tz.localize(datetime.combine(date, hours.start_time))
            end_time = tz.localize(datetime.combine(date, hours.end_time))
            
            while current_time + timedelta(minutes=service.duration) <= end_time:
                # Check if slot is available
                slot_end = current_time + timedelta(minutes=service.duration)
                is_available = not Booking.objects.filter(
                    business=business,
                    start_time__lt=slot_end,
                    end_time__gt=current_time,
                    status='confirmed'
                ).exists()
                
                if is_available:
                    slots.append(current_time.strftime('%H:%M'))
                
                current_time += timedelta(minutes=30)
            
            return JsonResponse({'slots': slots})
            
        except BusinessHours.DoesNotExist:
            return JsonResponse({'slots': [], 'message': 'Business is closed on this day'})
            
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)

def create_booking(request):
    """Create a new booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # ... booking creation logic to be implemented ...
    return JsonResponse({'success': True})

@login_required
def cancel_booking(request, booking_id):
    """Cancel an existing booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Only allow business owner or the customer who made the booking
    if request.user != booking.business.owner and request.user != booking.customer.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    if booking.status == 'cancelled':
        return JsonResponse({'error': 'Booking already cancelled'}, status=400)
    
    booking.status = 'cancelled'
    booking.save()
    
    # TODO: Handle refund logic here if payment was made
    
    return JsonResponse({'success': True})

@login_required
def business_hours(request):
    """Set business operating hours"""
    # Add view logic for setting business hours
    pass
