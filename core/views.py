from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import Business, Customer
from django.utils import timezone
from django.contrib import messages

def business_signup(request):
    """Business owner registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated business
            business = Business.objects.create(
                owner=user,
                name=request.POST['business_name'],
                email=request.POST['email'],
                phone=request.POST['phone']
            )
            login(request, user)
            return redirect('core:dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/signup.html', {'form': form})

@login_required
def business_dashboard(request):
    """Main dashboard for business owners"""
    try:
        business = Business.objects.get(owner=request.user)
        context = {
            'business': business,
            'services': business.services.all(),
            'upcoming_bookings': business.booking_set.select_related('service', 'customer').filter(
                start_time__gte=timezone.now()
            ).order_by('start_time')[:5]
        }
        return render(request, 'core/dashboard.html', context)
    except Business.DoesNotExist:
        messages.warning(request, "Please complete your business profile first.")
        return redirect('core:signup')

def landing_page(request):
    """Public landing page"""
    return render(request, 'core/landing.html', {
        'businesses': Business.objects.all()[:5]
    })
