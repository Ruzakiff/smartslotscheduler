from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from core.models import Business, Customer
from .models import Service, Booking, BusinessHours
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pytz
import json
from getcalendar import CalendarService
from .services import DjangoCalendarService


# Create your views here.

# Initialize calendar service
calendar_service = CalendarService()

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
    address = request.GET.get('address')
    unit = request.GET.get('unit')
    
    if not service_id:
        return JsonResponse({'error': 'Service ID is required'}, status=400)
    
    try:
        # Initialize calendar service with business
        calendar_service = DjangoCalendarService(business)
        
        # Construct full address if provided
        full_address = f"{address}{f' Unit {unit}' if unit else ''}" if address else None
        
        # Get available slots
        available_slots = calendar_service.get_available_slots(
            date_str,
            service_id,
            destination_address=full_address
        )
        
        return JsonResponse({'slots': available_slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

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

def hold_slot(request):
    """API endpoint to hold a time slot temporarily"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        result = calendar_service.hold_slot(
            data['date'],
            data['time'],
            data['service_type']
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_calendar_slots(request):
    """API endpoint to get available calendar slots"""
    date = request.GET.get('date')
    service_id = request.GET.get('service')
    address = request.GET.get('address')
    unit = request.GET.get('unit')
    
    if not service_id:
        return JsonResponse({'error': 'Service ID is required'}, status=400)
    
    try:
        # Get service from database
        service = Service.objects.get(id=service_id)
        
        # Construct full address
        full_address = f"{address}{f' Unit {unit}' if unit else ''}"
        
        available_slots = calendar_service.get_available_slots(
            date, 
            service.duration,  # Use duration from service model
            destination_address=full_address
        )
        return JsonResponse({'slots': available_slots})
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def create_calendar_booking(request):
    """API endpoint to create a calendar booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        booking_data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['date', 'time', 'service_id', 'name']
        missing_fields = [field for field in required_fields if field not in booking_data]
        
        if missing_fields:
            return JsonResponse(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 
                status=400
            )

        # Get service from database
        try:
            service = Service.objects.get(id=booking_data['service_id'])
        except Service.DoesNotExist:
            return JsonResponse({'error': 'Service not found'}, status=404)

        # Update booking data with service information
        booking_data['service_type'] = service.name
        booking_data['duration'] = service.duration

        # Create the booking
        result = calendar_service.create_booking(booking_data)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def release_slot(request):
    """API endpoint to release a held time slot"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        if not data or 'date' not in data or 'time' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing date or time in request'
            }, status=400)

        slot_key = f"{data['date']} {data['time']}"
        
        # Remove the hold if it exists
        if slot_key in calendar_service.pending_bookings:
            del calendar_service.pending_bookings[slot_key]
            return JsonResponse({
                'status': 'success',
                'message': 'Hold released successfully'
            })
        
        return JsonResponse({
            'status': 'success',
            'message': 'No hold found to release'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
