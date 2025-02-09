from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    # Public booking URLs
    path('<slug:booking_url>/', views.booking_page, name='booking_page'),
    path('api/slots/<int:business_id>/', views.get_available_slots, name='get_slots'),
    path('booking/confirm/', views.create_booking, name='create_booking'),
]