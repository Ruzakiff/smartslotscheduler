from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import Business, Customer
from .models import Service, Booking
from datetime import datetime, timedelta

# Create your views here.

def booking_page(request, booking_url):
    """Main booking page for a specific business"""
    business = get_object_or_404(Business, booking_url=booking_url)
    services = Service.objects.filter(business=business, active=True)
    
    return render(request, 'scheduler/booking_page.html', {
        'business': business,
        'services': services,
    })

def get_available_slots(request, business_id):
    """AJAX endpoint to get available time slots"""
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')
    
    if not date_str or not service_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    slots = []
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Simple slot generation (9 AM to 5 PM)
    start = date.replace(hour=9, minute=0)
    while start.hour < 17:
        slots.append(start.strftime('%H:%M'))
        start += timedelta(minutes=60)
    
    return JsonResponse({'slots': slots})

def create_booking(request):
    """Handle the booking form submission"""
    if request.method == 'POST':
        try:
            # Get or create customer
            customer, created = Customer.objects.get_or_create(
                email=request.POST['email'],
                defaults={
                    'name': request.POST['name'],
                    'phone': request.POST['phone']
                }
            )
            
            # Create booking
            start_time = datetime.strptime(
                f"{request.POST['date']} {request.POST['time']}", 
                '%Y-%m-%d %H:%M'
            )
            service = Service.objects.get(id=request.POST['service'])
            
            booking = Booking.objects.create(
                business_id=request.POST['business'],
                service=service,
                customer=customer,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=service.duration),
                status='pending'
            )
            
            return JsonResponse({
                'success': True, 
                'booking_id': booking.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
