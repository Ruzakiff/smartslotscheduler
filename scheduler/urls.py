from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    # API endpoints
    path('api/slots/<int:business_id>/', views.get_available_slots, name='get_slots'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # This should be last as it's a catch-all pattern
    path('<str:booking_url>/', views.booking_page, name='booking_page'),
    path('api/hold-slot', views.hold_slot, name='hold_slot'),
    path('api/available-slots', views.get_calendar_slots, name='get_calendar_slots'),
    path('api/create-booking', views.create_calendar_booking, name='create_calendar_booking'),
    path('api/release-hold', views.release_slot, name='release_slot'),
]