from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import Business, Customer
from django.utils import timezone
from django.contrib import messages
from scheduler.models import Service, BusinessHours, Booking
from datetime import time
from django.contrib.auth.models import User
from django.db import transaction

def business_signup(request):
    """Business registration & onboarding"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=request.POST['email'],
                    email=request.POST['email'],
                    password=request.POST['password1']
                )
                
                # Create business with cleaned URL
                business_name = request.POST['business_name']
                booking_url = request.POST['business_name'].lower()
                booking_url = ''.join(c for c in booking_url if c.isalnum() or c == '-')
                booking_url = booking_url.replace(' ', '-')
                
                business = Business.objects.create(
                    owner=user,
                    name=business_name,
                    email=request.POST['email'],
                    phone=request.POST['phone'],
                    booking_url=booking_url
                )
                
                messages.success(request, "Account created successfully! Please log in.")
                return redirect('core:login')
                
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
    
    return render(request, 'core/signup.html')

@login_required
def business_dashboard(request):
    """Business owner's dashboard"""
    business = get_object_or_404(Business, owner=request.user)
    services = Service.objects.filter(business=business)
    upcoming_bookings = Booking.objects.filter(
        business=business,
        start_time__gte=timezone.now()
    ).order_by('start_time')[:5]
    
    return render(request, 'core/dashboard.html', {
        'business': business,
        'services': services,
        'upcoming_bookings': upcoming_bookings,
    })

def landing_page(request):
    """Homepage showing list of businesses and signup option"""
    businesses = Business.objects.all()
    return render(request, 'core/landing.html', {
        'businesses': businesses
    })

@login_required
def add_service(request):
    """Add a new service for the business"""
    try:
        business = Business.objects.get(owner=request.user)
        
        if request.method == 'POST':
            service = Service.objects.create(
                business=business,
                name=request.POST['name'],
                duration=int(request.POST['duration']),
                price=float(request.POST['price']),
                description=request.POST.get('description', ''),
                active=True
            )
            messages.success(request, f"Service '{service.name}' added successfully!")
            return redirect('core:dashboard')
            
        return render(request, 'core/service_form.html', {'business': business})
        
    except Business.DoesNotExist:
        messages.error(request, "Please create a business profile first")
        return redirect('core:signup')

@login_required
def edit_service(request, service_id):
    """Edit an existing service"""
    service = get_object_or_404(Service, id=service_id, business__owner=request.user)
    
    if request.method == 'POST':
        service.name = request.POST['name']
        service.duration = int(request.POST['duration'])
        service.price = float(request.POST['price'])
        service.description = request.POST.get('description', '')
        service.active = request.POST.get('active') == 'on'
        service.save()
        
        messages.success(request, f"Service '{service.name}' updated successfully!")
        return redirect('core:dashboard')
        
    return render(request, 'core/service_form.html', {
        'service': service,
        'business': service.business
    })

@login_required
def delete_service(request, service_id):
    """Delete a service"""
    service = get_object_or_404(Service, id=service_id, business__owner=request.user)
    
    if request.method == 'POST':
        name = service.name
        service.delete()
        messages.success(request, f"Service '{name}' deleted successfully!")
        return redirect('core:dashboard')
        
    return render(request, 'core/service_delete.html', {
        'service': service,
        'business': service.business
    })

@login_required
def business_hours(request):
    """Manage business operating hours"""
    business = get_object_or_404(Business, owner=request.user)
    
    if request.method == 'POST':
        # Clear existing hours
        BusinessHours.objects.filter(business=business).delete()
        
        # Create new hours for each day
        for day in range(7):  # 0 = Monday, 6 = Sunday
            is_closed = request.POST.get(f'closed_{day}') == 'on'
            if not is_closed:
                start = request.POST.get(f'start_{day}')
                end = request.POST.get(f'end_{day}')
                if start and end:
                    BusinessHours.objects.create(
                        business=business,
                        day_of_week=day,
                        start_time=start,
                        end_time=end,
                        is_closed=is_closed
                    )
    
    # Get existing hours
    hours_dict = {}
    existing_hours = BusinessHours.objects.filter(business=business)
    
    # Create a dictionary with default values
    for day in range(7):
        try:
            hour = existing_hours.get(day_of_week=day)
            hours_dict[day] = {
                'start_time': hour.start_time,
                'end_time': hour.end_time,
                'is_closed': hour.is_closed
            }
        except BusinessHours.DoesNotExist:
            # Default: 9 AM to 5 PM, closed on weekends
            hours_dict[day] = {
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'is_closed': day >= 5  # Saturday and Sunday
            }
    
    return render(request, 'core/business_hours.html', {
        'business': business,
        'hours': hours_dict,
        'days': BusinessHours.DAYS_OF_WEEK
    })

@login_required
def logout_view(request):
    """Custom logout view that accepts GET requests"""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('core:landing')
